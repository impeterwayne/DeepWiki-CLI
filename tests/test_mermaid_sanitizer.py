"""
Regression tests for the Mermaid sanitizer.

Every case below is a real DeepWiki diagram that Mermaid refused to parse.
Run with `pytest tests/` or directly with `python tests/test_mermaid_sanitizer.py`.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepwiki_crawler import sanitize_mermaid_block, sanitize_all_mermaids_in_markdown


def _assert_clean(fixed: str):
    """No repaired diagram may keep the constructs Mermaid chokes on."""
    for line in fixed.split("\n"):
        assert not re.search(r'(?<![A-Za-z0-9_\-\$\]\)\}\[\(\{>/\\])\[["A-Za-z]', line), line
        assert '"]["' not in line, line


def test_anonymous_bracket_nodes_get_ids():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    [ProjectConfig] --> [CapabilitiesFile]\n'
        '    [capabilities.yaml] -.-> Parser["parse()"]\n'
    )
    assert "ProjectConfig[" in fixed and "CapabilitiesFile[" in fixed
    assert "capabilities_yaml[" in fixed
    _assert_clean(fixed)


def test_bracket_reference_inside_a_quoted_label_is_left_alone():
    """The label already parses; rewriting its inner `[...]` would nest brackets."""
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    CMD["wrapCommand() [src/cli/commands/wrap.ts]"] --> B\n'
    )
    assert 'CMD["wrapCommand() [src/cli/commands/wrap.ts]"]' in fixed


def test_style_target_is_reduced_to_a_bare_id():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    [capabilities.yaml] --- A\n'
        '    style [capabilities.yaml] stroke-dasharray: 5 5\n'
    )
    assert "style capabilities_yaml stroke-dasharray: 5 5" in fixed


def test_unquoted_label_with_parentheses_gets_quoted():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    E --> F[spawn(cmd, args, ...)]\n'
        '    K --> L[Capabilities (from cache)]\n'
    )
    assert 'F["spawn(cmd, args, ...)"]' in fixed
    assert 'L["Capabilities (from cache)"]' in fixed


def test_cylinder_shape_survives_quoting():
    fixed = sanitize_mermaid_block('graph TD\n    F --> G[("CapaDatabase (tool_calls)")]\n')
    assert 'G[("CapaDatabase (tool_calls)")]' in fixed


def test_bare_quoted_strings_become_nodes_but_edge_labels_do_not():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    "User Initiates Auth" -.-> "OAuth2Manager.run()"\n'
        '    D -- "SessionInfo (cached)" --> E\n'
        '    S -->|"Returns path + SHA"| M\n'
    )
    assert 'User_Initiates_Auth["User Initiates Auth"]' in fixed
    assert '-- "SessionInfo (cached)" -->' in fixed
    assert '-->|"Returns path + SHA"|' in fixed


def test_quoted_id_followed_by_a_label_is_not_duplicated():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    "IEditorService"["IEditorService (impl)"] --> "B"["B"]\n'
    )
    assert 'IEditorService["IEditorService (impl)"]' in fixed
    assert '"]["' not in fixed


def test_bracket_wrapped_ids_are_collapsed():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    [Agent]["AI Agent (Copilot)"] --> B\n'
        '    [McpService] ["IMcpService (McpService)"]\n'
        '    [TestRunner] --> [EnvCheck{"Environment?"}]\n'
    )
    assert 'Agent["AI Agent (Copilot)"]' in fixed
    assert 'McpService["IMcpService (McpService)"]' in fixed
    assert 'EnvCheck{"Environment?"}' in fixed


def test_unquoted_edge_label_with_parentheses_gets_quoted():
    fixed = sanitize_mermaid_block('graph TD\n    A -->|loadBindings()| B\n')
    assert '-->|"loadBindings()"|' in fixed


def test_bracketed_edge_label_is_not_turned_into_a_node():
    fixed = sanitize_mermaid_block('graph TB\n    A -->|["ID=\'*\'"]| B\n')
    assert "|\"ID='*'\"|" in fixed


def test_subgraph_titles_always_get_an_id():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    subgraph "Natural Language Space"\n'
        '    end\n'
        '    subgraph Prerendering phase (Next.js Server)\n'
        '    end\n'
    )
    assert 'Natural_Language_Space ["Natural Language Space"]' in fixed
    assert 'Prerendering_phase_Next_js_Server ["Prerendering phase (Next.js Server)"]' in fixed


def test_subgraph_id_never_collides_with_a_node_id():
    """A subgraph sharing an id with a node makes Dagre report a cycle."""
    fixed = sanitize_mermaid_block(
        'graph LR\n'
        '    subgraph "Registry"\n'
        '        Registry["SessionsProvidersService"]\n'
        '    end\n'
    )
    assert 'subgraph Registry_group ["Registry"]' in fixed
    assert 'Registry["SessionsProvidersService"]' in fixed


def test_node_id_colliding_with_a_mermaid_keyword_is_renamed():
    fixed = sanitize_mermaid_block(
        'graph TD\n'
        '    graph["langgraph"]\n'
        '    call["call()"]\n'
        '    call --> graph\n'
    )
    assert fixed.startswith("graph TD")
    assert 'graph_node["langgraph"]' in fixed
    assert "call_node --> graph_node" in fixed


def test_anonymous_rhombus_node_gets_an_id():
    fixed = sanitize_mermaid_block('graph LR\n    A -->|fields| {alloc, dealloc}\n')
    assert 'alloc_dealloc{"alloc, dealloc"}' in fixed


def test_markdown_backticks_inside_a_label_are_neutralised():
    fixed = sanitize_mermaid_block('graph TD\n    C["`next/image` component (x.tsx)"]\n')
    assert "`" not in fixed


def test_class_diagram_relations_use_bare_ids():
    fixed = sanitize_mermaid_block(
        'classDiagram\n'
        '    class "FastAPI" as FastAPI_Entity {\n'
        '        +str title\n'
        '    }\n'
        '    class "BaseModelWithConfig" {\n'
        '        +int x\n'
        '    }\n'
        '    "BaseModelWithConfig" <|-- "OpenAPI"\n'
    )
    assert 'class FastAPI_Entity["FastAPI"] {' in fixed
    assert 'class BaseModelWithConfig["BaseModelWithConfig"] {' in fixed
    assert "BaseModelWithConfig <|-- OpenAPI" in fixed


def test_state_diagram_quoted_states_are_declared():
    fixed = sanitize_mermaid_block(
        'stateDiagram-v2\n'
        '    [*] --> "Pending" : registryAddCommand\n'
        '    "Pending" --> "installed" : installRegistry (Success)\n'
        '    state "installed" {\n'
        '        L1: status = \'installed\'\n'
        '    }\n'
    )
    assert 'state "Pending" as Pending' in fixed
    assert "[*] --> Pending : registryAddCommand" in fixed
    assert "state installed {" in fixed
    assert "L1: status = 'installed'" in fixed  # label text preserved


def test_sequence_diagram_quoted_participants():
    fixed = sanitize_mermaid_block(
        'sequenceDiagram\n'
        '    participant "ASGI Server"\n'
        '    participant "Flask.__call__" as App\n'
        '    "ASGI Server"->>App: scope, receive, send\n'
        '    Ctx>>App: push context\n'
    )
    assert 'participant ASGI_Server as "ASGI Server"' in fixed
    assert 'participant App as "Flask.__call__"' in fixed
    assert "ASGI_Server->>App: scope, receive, send" in fixed
    assert "Ctx->>App: push context" in fixed


def test_class_diagram_operators_in_a_flowchart_become_links():
    fixed = sanitize_mermaid_block('graph LR\n    ["A"] <|-- ["B"]\n')
    assert "---" in fixed and "<|--" not in fixed


def test_non_flowchart_diagrams_are_passed_through():
    block = "erDiagram\n    CUSTOMER ||--o{ ORDER : places\n"
    assert sanitize_mermaid_block(block) == block


def test_markdown_wrapper_rewrites_every_block():
    md = 'intro\n\n```mermaid\ngraph TD\n    [A] --> [B]\n```\n\ntail\n'
    out = sanitize_all_mermaids_in_markdown(md)
    assert out.count("```mermaid") == 1
    assert "A[" in out and "B[" in out
    assert out.startswith("intro") and out.rstrip().endswith("tail")


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print(f"\n{failures} failed")
    sys.exit(1 if failures else 0)
