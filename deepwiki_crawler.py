"""
DeepWiki CLI & Crawler
=======================
An asynchronous documentation crawler for DeepWiki (and GitHub repositories) using Crawl4AI.
Extracts complete, high-fidelity documentation wikis with all Mermaid diagrams, tables,
collapsible sections, and source links intact.

Supports multi-format exports:
  - 'split': Individual Markdown files per chapter + Table of Contents (00_INDEX.md)
  - 'combined': Single monolithic Markdown file with master TOC & anchors
  - 'json': Structured JSON dataset with metadata for RAG pipelines & vector databases
"""

import os
import re
import sys
import json
import asyncio
import argparse
import warnings
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse

# Suppress noisy library dependency warnings
warnings.filterwarnings("ignore", message=".*urllib3.*or chardet.*")
warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
warnings.filterwarnings("ignore", category=UserWarning)


# Ensure Windows terminal handles UTF-8 properly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

console = Console(force_terminal=True, legacy_windows=False)


@dataclass
class WikiPageMeta:
    """Metadata for a documentation chapter/page."""
    index: int
    title: str
    url: str
    slug: str
    chapter_num: Optional[str] = None


@dataclass
class CrawledPage:
    """Result of crawling a single documentation page."""
    meta: WikiPageMeta
    markdown: str
    success: bool
    status_code: Optional[int] = 200
    error: Optional[str] = None
    char_count: int = 0
    word_count: int = 0
    mermaid_count: int = 0


# Mermaid keywords that cannot double as a node id.
_MERMAID_RESERVED = {
    "graph", "flowchart", "subgraph", "end", "class", "classdef", "click",
    "style", "linkstyle", "direction", "call", "href", "default", "interpolate",
}

# The subset of the above that can legitimately open a statement.
_MERMAID_STATEMENT_KEYWORDS = {
    "graph", "flowchart", "subgraph", "end", "class", "classdef", "click",
    "style", "linkstyle", "direction",
}

# Statement keywords whose argument is a free-form label, not a participant.
_SEQUENCE_BLOCK_KEYWORDS = {
    "loop", "alt", "else", "opt", "par", "and", "rect", "critical", "option",
    "break", "box", "end", "autonumber", "title", "note", "activate",
    "deactivate", "links", "link",
}


def clean_node_identifier(label: str) -> str:
    """Generates a clean alphanumeric identifier for a Mermaid node."""
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", label).strip("_")
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"node_{cleaned}"
    cleaned = cleaned[:40].strip("_") or "node"
    if cleaned.lower() in _MERMAID_RESERVED:
        cleaned = f"{cleaned}_node"
    return cleaned


# --------------------------------------------------------------------------- #
# Mermaid sanitizing helpers
#
# Every rewrite below runs on a *masked* line: each `"..."` literal is swapped
# for a `\x00S<n>\x00` placeholder first. Without masking, a label such as
# `CMD["wrapCommand() [src/cli/wrap.ts]"]` gets rewritten from the inside out
# and produces nested brackets that Mermaid cannot parse.
# --------------------------------------------------------------------------- #

_MASK_RE = re.compile(r"\x00S(\d+)\x00")

# Characters Mermaid tolerates inside an *unquoted* node label.
_SAFE_UNQUOTED_LABEL = re.compile(r"^[A-Za-z0-9_\s\.\-/]*$")

# Node shapes, longest opener first so `[[` wins over `[`.
_SHAPE_OPENERS = ("[[", "[(", "([", "((", "{{", "[/", "[\\", "[", "(", "{", ">")
_SHAPE_CLOSERS = {
    "[[": ("]]",),
    "[(": (")]",),
    "([": ("])",),
    "((": ("))",),
    "{{": ("}}",),
    "[/": ("/]", "\\]"),
    "[\\": ("\\]", "/]"),
    "[": ("]",),
    "(": (")",),
    "{": ("}",),
    ">": ("]",),
}

# A bracket group is only a *new* node when nothing node-like precedes it
# (a preceding `\x00` mask means it is the label of a quoted id, not a new node).
_NOT_A_NODE_PREFIX = "(?<![A-Za-z0-9_\\-\\$\\]\\)\\}\\[\\(\\{>/\\\\\x00])"

# classDiagram-only relations that DeepWiki sometimes emits inside a flowchart.
_CLASS_RELATION_IN_FLOWCHART = re.compile(r"<\|\.\.|\.\.\|>|<\|--|--\|>|\*--|--\*")


def _mask_quoted(line: str, store: List[str]) -> str:
    """Replaces every "..." literal with an opaque placeholder."""
    def _hide(match):
        # AI output sometimes double-escapes quotes: "\"Label\"" -> 'Label'
        label = match.group(1).replace('\\"', "'")
        # A backtick opens Mermaid's markdown-string mode; only a label that is
        # entirely wrapped in backticks is valid, the rest would break the lexer.
        if label.count("`") and not (
            label.count("`") == 2 and label.startswith("`") and label.endswith("`")
        ):
            label = label.replace("`", "'")
        store.append(label)
        return f"\x00S{len(store) - 1}\x00"

    return re.sub(r'"((?:[^"\\\n]|\\.)*)"', _hide, line)


def _unmask_quoted(text: str, store: List[str]) -> str:
    return _MASK_RE.sub(lambda m: '"' + store[int(m.group(1))] + '"', text)


def _new_mask(value: str, store: List[str]) -> str:
    store.append(value)
    return f"\x00S{len(store) - 1}\x00"


def _masked_value(token: str, store: List[str]) -> Optional[str]:
    match = _MASK_RE.fullmatch(token.strip())
    return store[int(match.group(1))] if match else None


def _quote_unsafe_labels(line: str, store: List[str]) -> str:
    """
    Wraps node labels in quotes when they contain characters Mermaid rejects
    unquoted, e.g. `F[spawn(cmd, args, ...)]` -> `F["spawn(cmd, args, ...)"]`.
    Shape delimiters are preserved, so `G[(...)]` stays a cylinder.
    """
    ident_re = re.compile(r"[A-Za-z0-9_]+")
    out: List[str] = []
    i, n = 0, len(line)

    while i < n:
        match = ident_re.match(line, i)
        if not match:
            out.append(line[i])
            i += 1
            continue

        ident, body_start = match.group(0), match.end()
        opener = next((o for o in _SHAPE_OPENERS if line.startswith(o, body_start)), None)
        if opener is None:
            out.append(ident)
            i = body_start
            continue

        depth = sum(1 for ch in opener if ch in "[({") or 1
        k = body_start + len(opener)
        closer = content_end = None

        while k < n:
            ch = line[k]
            if ch in "[({":
                depth += 1
            elif ch in "])}":
                depth -= 1
                if depth == 0:
                    for candidate in _SHAPE_CLOSERS[opener]:
                        if line.startswith(candidate, k - len(candidate) + 1):
                            closer, content_end = candidate, k - len(candidate) + 1
                            break
                    if closer is None:
                        closer, content_end = ch, k
                    break
            k += 1

        if content_end is None:  # unbalanced - leave the line alone
            out.append(ident)
            i = body_start
            continue

        content = line[body_start + len(opener):content_end]
        if not (_MASK_RE.fullmatch(content.strip()) or _SAFE_UNQUOTED_LABEL.match(content)):
            label = _unmask_quoted(content, store).replace('"', "'").strip()
            content = _new_mask(label, store)

        out.append(ident + opener + content + closer)
        i = content_end + len(closer)

    return "".join(out)


def _normalize_edge_labels(line: str, store: List[str]) -> str:
    """
    Edge labels are plain text, never nodes: `-->|["ID='*'"]|` -> `-->|"ID='*'"|`,
    and `-->|loadBindings()|` has to be quoted or the parentheses break the parse.
    """
    def _fix(match):
        inner = match.group(1).strip()
        bracketed = re.fullmatch(r"\[\s*(.*?)\s*\]", inner, re.S)
        if bracketed:
            inner = bracketed.group(1).strip()
        if _MASK_RE.fullmatch(inner):
            return f"|{inner}|"
        text = _unmask_quoted(inner, store).replace('"', "'").strip()
        return f"|{_new_mask(text, store)}|" if text else "||"

    return re.sub(r"\|([^|\n]*)\|", _fix, line)


def _collapse_bracketed_ids(line: str, store: List[str]) -> str:
    """
    DeepWiki writes node ids inside brackets and then attaches the real shape:
      `[EnvCheck{"Ready?"}]` -> `EnvCheck{"Ready?"}`
      `[Agent]["AI Agent"]`  -> `Agent["AI Agent"]`
      `[McpService] ["IMcpService"]` -> `McpService["IMcpService"]`
    """
    line = re.sub(
        _NOT_A_NODE_PREFIX + r"\[\s*([A-Za-z0-9_]+\s*[\({\[]\x00S\d+\x00[\)\}\]])\s*\]",
        lambda m: m.group(1),
        line,
    )
    return re.sub(
        _NOT_A_NODE_PREFIX + r"\[([^\[\]\x00\n]+)\]\s*(?=[\[\({])",
        lambda m: clean_node_identifier(m.group(1)),
        line,
    )


def _convert_anonymous_nodes(line: str, store: List[str]) -> str:
    """`["Label"]` / `[Label]` with no node id -> `Label_id["Label"]`."""
    def _from_quoted(match):
        label = store[int(match.group(1))]
        return f"{clean_node_identifier(label)}[\x00S{match.group(1)}\x00]"

    line = re.sub(_NOT_A_NODE_PREFIX + r"\[\x00S(\d+)\x00\]", _from_quoted, line)

    def _from_unquoted(match):
        label = match.group(1).strip()
        if not label or label == "*":  # `[*]` is a state-diagram terminal
            return match.group(0)
        return f"{clean_node_identifier(label)}[{_new_mask(label, store)}]"

    line = re.sub(
        _NOT_A_NODE_PREFIX + r"\[([^\[\]\x00\n]+)\](?!\s*[\(\[\{])",
        _from_unquoted,
        line,
    )

    # Anonymous rhombus/round nodes: `--> {a, b, c}` -> `--> a_b_c{"a, b, c"}`.
    # Only after an edge or a label pipe, so labels like `A[foo (bar)]` are safe.
    def _from_unquoted_shape(match):
        prefix, opener, label, closer = match.groups()
        if _SHAPE_CLOSERS[opener][0] != closer:
            return match.group(0)
        label = label.strip()
        if not label:
            return match.group(0)
        return f"{prefix}{clean_node_identifier(label)}{opener}{_new_mask(label, store)}{closer}"

    return re.sub(
        r"(^\s*|[-=>.~|]\s*)([\{\(])([^\{\}\(\)\[\]\x00\n]+)([\}\)])",
        _from_unquoted_shape,
        line,
    )


def _convert_bare_quoted_nodes(line: str, store: List[str]) -> str:
    """
    Quoted strings standing in for node ids:
      `"A" --> "B"`            -> `A["A"] --> B["B"]`
      `"A"["A (impl)"]`        -> `A["A (impl)"]`
      `"A(...)" as Router --> ` -> `Router["A(...)"] --> `
    Edge labels (`-->|"text"|` and `-- "text" -->`) are left untouched.
    """
    # `"Label" as Id` -> `Id["Label"]`
    line = re.sub(
        r"(?<![\[\(\{>/\\|A-Za-z0-9_])\x00S(\d+)\x00\s+as\s+([A-Za-z0-9_]+)",
        lambda m: f"{m.group(2)}[\x00S{m.group(1)}\x00]",
        line,
    )
    # `"Id"["Label"]` -> `Id["Label"]`
    line = re.sub(
        r"(?<![\[\(\{>/\\|A-Za-z0-9_])\x00S(\d+)\x00\s*(?=[\[\({])",
        lambda m: clean_node_identifier(store[int(m.group(1))]),
        line,
    )

    protected = set()
    for match in re.finditer(r"\|\s*\x00S(\d+)\x00\s*\|", line):
        protected.add(int(match.group(1)))
    for match in re.finditer(r"(?:-{2,}|={2,}|-\.)(?![>xo])\s*\x00S(\d+)\x00\s*[-=.]", line):
        protected.add(int(match.group(1)))

    def _to_node(match):
        index = int(match.group(1))
        if index in protected:
            return match.group(0)
        return f"{clean_node_identifier(store[index])}[{match.group(0)}]"

    return re.sub(
        r"(?<![\[\(\{>/\\|])\x00S(\d+)\x00(?![\]\)\}/\\|])",
        _to_node,
        line,
    )


def _split_first_target(rest: str) -> Tuple[str, str]:
    """Splits `[capabilities.yaml] stroke-dasharray: 5 5` into target + remainder."""
    depth = 0
    for i, ch in enumerate(rest):
        if ch in "[({":
            depth += 1
        elif ch in "])}":
            depth -= 1
        elif ch.isspace() and depth == 0 and i > 0:
            return rest[:i], rest[i:]
    return rest, ""


def _node_ref_to_id(token: str, store: List[str]) -> str:
    """Reduces any node reference to the bare id `style`/`class`/`click` require."""
    token = token.strip()
    label = _masked_value(token, store)
    if label is not None:
        return clean_node_identifier(label)

    match = re.match(r"^([A-Za-z0-9_]+)[\[\(\{>]", token)
    if match:
        return match.group(1)

    match = re.match(r"^\[\s*(.*?)\s*\]$", token, re.S)
    if match:
        inner = match.group(1)
        return clean_node_identifier(_masked_value(inner, store) or inner)

    return token


def _sanitize_style_statement(rest: str, store: List[str]) -> str:
    target, remainder = _split_first_target(rest)
    ids = ",".join(_node_ref_to_id(part, store) for part in target.split(",") if part.strip())
    return (ids or target) + remainder


def _rename_reserved_ids(lines: List[str], reserved_ids: set) -> List[str]:
    """Renames node ids that collide with Mermaid keywords (e.g. a node called `graph`)."""
    renamed = []
    for position, line in enumerate(lines):
        indent = len(line) - len(line.lstrip())

        def _rename(match):
            # Leave statement keywords alone: `graph TD`, `subgraph Foo`, `end`.
            at_line_start = match.start() == indent
            followed_by_shape = match.end() < len(line) and line[match.end()] in "[({>"
            is_statement = match.group(0).lower() in _MERMAID_STATEMENT_KEYWORDS
            if position == 0 or (is_statement and at_line_start and not followed_by_shape):
                return match.group(0)
            return f"{match.group(0)}_node"

        pattern = r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(i) for i in reserved_ids) + r")(?![A-Za-z0-9_])"
        renamed.append(re.sub(pattern, _rename, line))
    return renamed


def _sanitize_flowchart(lines: List[str]) -> str:
    store: List[str] = []
    out: List[str] = []
    reserved_ids = set()
    masked_lines = [_mask_quoted(l, store) for l in lines]

    # A subgraph id that collides with a node id makes Dagre report a cycle,
    # so the ids already spoken for have to be known up front.
    taken_ids = set()
    for masked in masked_lines:
        if re.match(r"^\s*(?:subgraph|style|class|click|linkStyle|classDef)\b", masked):
            continue
        for m in re.finditer(r"(?<![A-Za-z0-9_])([A-Za-z0-9_]+)(?=[\[\(\{>])", masked):
            taken_ids.add(m.group(1))

    for line in masked_lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("%%"):
            out.append(line)
            continue

        # A subgraph always needs a bare id; the title becomes a quoted label:
        #   `subgraph "Name"`                  -> `Name ["Name"]`
        #   `subgraph "Id" ["Label"]`          -> `Id ["Label"]`
        #   `subgraph Prerendering (Server)`   -> `Prerendering_Server ["Prerendering (Server)"]`
        m_sub = re.match(r"^(\s*subgraph\s+)(\S.*?)\s*$", line)
        if m_sub:
            rest = m_sub.group(2)
            m_split = re.match(r"^(.*?)\s*\[\s*(.*?)\s*\]$", rest, re.S)
            id_part, label_part = m_split.groups() if m_split else (rest, None)

            title = _masked_value(id_part, store)
            if title is None:
                title = _unmask_quoted(id_part, store).replace('"', "'")
            if label_part is None:
                label = title
            else:
                label = _masked_value(label_part, store)
                if label is None:
                    label = _unmask_quoted(label_part, store).replace('"', "'")

            sub_id = clean_node_identifier(title)
            while sub_id in taken_ids:
                sub_id += "_group"
            taken_ids.add(sub_id)

            out.append(f"{m_sub.group(1)}{sub_id} [{_new_mask(label, store)}]")
            continue

        # `style`/`class`/`click`/`linkStyle` only accept bare node ids.
        m_style = re.match(r"^(\s*)(style|class|click|linkStyle|classDef)\s+(.*)$", line)
        if m_style:
            out.append(
                f"{m_style.group(1)}{m_style.group(2)} "
                + _sanitize_style_statement(m_style.group(3), store)
            )
            continue

        # classDiagram relations leaked into a flowchart: keep the link, drop the arrowhead.
        line = _CLASS_RELATION_IN_FLOWCHART.sub("---", line)

        line = _normalize_edge_labels(line, store)
        line = _collapse_bracketed_ids(line, store)
        line = _convert_bare_quoted_nodes(line, store)
        line = _convert_anonymous_nodes(line, store)
        line = _quote_unsafe_labels(line, store)

        for match in re.finditer(r"(?<![A-Za-z0-9_])([A-Za-z0-9_]+)(?=[\[\({>])", line):
            if match.group(1).lower() in _MERMAID_RESERVED:
                reserved_ids.add(match.group(1))

        out.append(line)

    if reserved_ids:
        out = _rename_reserved_ids(out, reserved_ids)

    return "\n".join(_unmask_quoted(line, store) for line in out)


def _sanitize_sequence_diagram(lines: List[str]) -> str:
    """
    Mermaid rejects a quoted string as a participant id, so
    `"ASGI Server"->>"websocket_session()": msg` fails. Quoted names become ids
    and are declared once via `participant Id as "Name"`.
    """
    store: List[str] = []
    names: Dict[str, str] = {}
    out: List[str] = []
    declared = set()

    def _to_id(match):
        label = store[int(match.group(1))]
        return names.setdefault(label, clean_node_identifier(label))

    for raw_line in lines:
        line = _mask_quoted(raw_line, store)

        # participant ["Name"] / participant "Name" -> participant Id as "Name"
        m_part = re.match(
            r"^(\s*)(participant|actor)\s+\[?\s*(\x00S\d+\x00)\s*\]?"
            r"(?:\s+as\s+([A-Za-z0-9_]+))?\s*$",
            line,
        )
        if m_part:
            label = _masked_value(m_part.group(3), store) or ""
            ident = m_part.group(4) or names.setdefault(label, clean_node_identifier(label))
            names.setdefault(label, ident)
            declared.add(ident)
            out.append(f"{m_part.group(1)}{m_part.group(2)} {ident} as {m_part.group(3)}")
            continue

        # Message text lives right of the first `:` and must survive untouched.
        head, sep, tail = line.partition(":")

        if head.strip().split(" ")[0].lower() not in _SEQUENCE_BLOCK_KEYWORDS:
            head = re.sub(r'\[\x00S(\d+)\x00\]', _to_id, head)
            head = _MASK_RE.sub(_to_id, head)
            # `A>>B` is not a valid arrow; Mermaid needs `A->>B`.
            head = re.sub(r"(?<![-<>])>>", "->>", head)

        out.append(head + sep + tail)

    missing = [
        f'    participant {ident} as "{label}"'
        for label, ident in names.items()
        if ident not in declared
    ]
    if missing and out:
        out = out[:1] + missing + out[1:]

    return "\n".join(_unmask_quoted(line, store) for line in out)


def _sanitize_state_diagram(lines: List[str]) -> str:
    """
    Mermaid state diagrams cannot use a quoted string as a state id, so
    `[*] --> "Pending"` fails. Quoted names are turned into ids and declared
    once via `state "Pending" as Pending`.
    """
    store: List[str] = []
    names: Dict[str, str] = {}
    out: List[str] = []

    for raw_line in lines:
        line = _mask_quoted(raw_line, store)

        # `state "Name" as id` is already valid - leave it (and its id) alone.
        if re.match(r"^\s*state\s+\x00S\d+\x00\s+as\s+", line):
            out.append(_unmask_quoted(line, store))
            continue

        # Everything right of the first `:` is free-form label text.
        head, sep, tail = line.partition(":")

        def _to_id(match):
            label = store[int(match.group(1))]
            return names.setdefault(label, clean_node_identifier(label))

        out.append(_MASK_RE.sub(_to_id, head) + sep + _unmask_quoted(tail, store))

    if names and out:
        indent = " " * 4
        declarations = [f'{indent}state "{label}" as {ident}' for label, ident in names.items()]
        out = out[:1] + declarations + out[1:]

    return "\n".join(out)


def _sanitize_class_diagram(lines: List[str]) -> str:
    """
    `class "FastAPI" as FastAPI_Entity {` and `["IChatService"] --> ["ChatModel"]`
    are both invalid; class ids must be bare, with the display name as a label.
    """
    store: List[str] = []
    names: Dict[str, str] = {}
    declared = set()
    out: List[str] = []

    def _to_id(match):
        label = store[int(match.group(1))]
        return names.setdefault(label, clean_node_identifier(label))

    for raw_line in lines:
        line = _mask_quoted(raw_line, store)

        # class "Name" [as Id] [{] -> class Id["Name"] [{]
        m_class = re.match(
            r"^(\s*class\s+)(\x00S(\d+)\x00)(?:\s+as\s+([A-Za-z0-9_]+))?\s*(\{?)\s*$", line
        )
        if m_class:
            label = store[int(m_class.group(3))]
            ident = m_class.group(4) or clean_node_identifier(label)
            names[label] = ident
            declared.add(ident)
            brace = f" {m_class.group(5)}" if m_class.group(5) else ""
            out.append(f"{m_class.group(1)}{ident}[{m_class.group(2)}]{brace}")
            continue

        if re.match(r"^\s*(?:note|click|link|callback|cssClass|style|%%)", line):
            out.append(line)
            continue

        head, sep, tail = line.partition(":")
        head = re.sub(r'\[\x00S(\d+)\x00\]', _to_id, head)
        head = re.sub(_NOT_A_NODE_PREFIX + r"\[([A-Za-z0-9_][A-Za-z0-9_\s\.\-/]*)\]",
                      lambda m: clean_node_identifier(m.group(1)), head)
        # `"BaseModel" <|-- "OpenAPI"` - relations cannot use quoted class names.
        head = _MASK_RE.sub(_to_id, head)
        out.append(head + sep + tail)

    # Keep the original display name for any class whose id had to be rewritten.
    out += [
        f'    class {ident}["{label}"]'
        for label, ident in names.items()
        if ident not in declared and ident != label
    ]
    return "\n".join(_unmask_quoted(line, store) for line in out)


def sanitize_mermaid_block(block: str) -> str:
    """
    Cleans and repairs syntax issues produced by AI-generated Mermaid diagrams:
      1. Anonymous bracket nodes: `["Label"]` / `[Label]` -> `NodeID["Label"]`
      2. Bare quoted nodes: `"A" --> "B"` -> `A["A"] --> B["B"]`
      3. Unquoted labels holding parentheses/commas: `F[spawn(a, b)]` -> `F["spawn(a, b)"]`
      4. Bracketed references inside quoted labels are left intact (no nesting)
      5. Bracket-wrapped ids: `[Agent]["AI Agent"]` -> `Agent["AI Agent"]`
      6. `style`/`class`/`click` targets reduced to bare node ids
      7. Node ids colliding with Mermaid keywords (`graph`, `end`, ...) renamed
      8. Quoted subgraph titles, state names, class names and sequence
         participants given real ids with the original text kept as the label
    """
    lines = block.strip().split("\n")
    if not lines:
        return block

    header = next((l.strip() for l in lines if l.strip() and not l.strip().startswith("%%")), "")

    if header.startswith("sequenceDiagram"):
        return _sanitize_sequence_diagram(lines)
    if header.startswith("stateDiagram"):
        return _sanitize_state_diagram(lines)
    if header.startswith("classDiagram"):
        return _sanitize_class_diagram(lines)
    if header.startswith("graph") or header.startswith("flowchart"):
        return _sanitize_flowchart(lines)

    return block


def sanitize_all_mermaids_in_markdown(md_text: str) -> str:
    """Finds all Mermaid code blocks in Markdown and cleans their syntax."""
    def _repl(match):
        raw_code = match.group(1)
        try:
            fixed_code = sanitize_mermaid_block(raw_code)
        except Exception:
            fixed_code = raw_code  # never lose a diagram to a sanitizer bug
        return f"```mermaid\n{fixed_code.strip()}\n```"

    return re.sub(r'```mermaid([\s\S]*?)```', _repl, md_text)


def is_repo_path(path: str) -> bool:
    """Checks if a string looks like a valid repository relative file path."""
    path = path.strip()
    if not path or path.startswith(('http://', 'https://', '#', 'mailto:', 'ftp:', 'chapters/', './chapters/')):
        return False
    if path.endswith('00_INDEX.md'):
        return False
    # Avoid strings with characters invalid in clean repository paths
    if any(c in path for c in ['<', '>', '"', "'", '`', ' ', '\t', '\n']):
        return False
    base = os.path.basename(path.replace('\\', '/'))
    if '.' in base or '/' in path or '\\' in path or path.startswith('.'):
        return True
    return False


def make_github_file_url(owner: str, repo: str, file_path: str, lines: Optional[str] = None, branch: str = "HEAD") -> str:
    """Constructs a GitHub blob URL pointing directly to a repository file and optional line range."""
    file_path = file_path.strip().lstrip('/').replace('\\', '/')
    base = f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}"
    if not lines:
        return base
    m = re.search(r'(\d+)(?:-(\d+))?', lines)
    if m:
        start = m.group(1)
        end = m.group(2)
        if end and end != start:
            return f"{base}#L{start}-L{end}"
        else:
            return f"{base}#L{start}"
    return base


def convert_markdown_links_to_github(text: str, owner: str, repo: str, branch: str = "HEAD") -> str:
    """
    Transforms source file references, relative file paths, and in-text line citations
    in Markdown into clickable, direct GitHub URLs.
    
    Preserves:
      - Mermaid diagrams
      - Local inter-chapter links (e.g. chapters/01_....md)
      - In-page anchors (e.g. #1.1)
      - External web URLs
    """
    # 1. Protect Mermaid diagram blocks from link modifications
    mermaid_blocks = []
    def _save_mermaid(m):
        mermaid_blocks.append(m.group(0))
        return f"<!--MERMAID_BLOCK_{len(mermaid_blocks) - 1}-->"

    text = re.sub(r'```mermaid[\s\S]*?```', _save_mermaid, text)

    # 2. Backtick file followed by line range citation: `path/to/file` [58-80]()
    def _repl_backtick_line(m):
        fpath = m.group(2).strip()
        space = m.group(3)
        lines = m.group(4).strip()
        if is_repo_path(fpath):
            url = make_github_file_url(owner, repo, fpath, lines, branch)
            return f'`{fpath}`{space}[{lines}]({url})'
        return m.group(0)

    text = re.sub(r'(`([^`\n]+)`)(\s*)\[(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)\]\(\)', _repl_backtick_line, text)

    # 3. Convert markdown links: [label](url)
    def _repl_link(m):
        label = m.group(1)
        url = m.group(2).strip()

        # If URL is already absolute web link or anchor or chapter link, preserve it
        if url.startswith(('http://', 'https://', '#', 'mailto:', 'ftp:', 'chapters/', './chapters/')) or url.endswith('00_INDEX.md'):
            return m.group(0)

        # Empty URL: [src/vs/code/app.ts:58-80]() or [package.json]()
        if not url:
            clean_label = label.strip()
            # Match path:start-end or path:start or path:start-end, start-end
            colon_match = re.match(r'^([a-zA-Z0-9_.\-\/\\]+):(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)$', clean_label)
            if colon_match:
                fpath = colon_match.group(1)
                lines = colon_match.group(2)
                if is_repo_path(fpath):
                    gh_url = make_github_file_url(owner, repo, fpath, lines, branch)
                    return f'[{label}]({gh_url})'
            elif is_repo_path(clean_label):
                gh_url = make_github_file_url(owner, repo, clean_label, branch=branch)
                return f'[{label}]({gh_url})'
            return m.group(0)

        # Non-empty relative URL: [label](extensions/auth/auth.css) or [label](path#L10-L20) or [label](path:10-20)
        lines = None
        fpath = url
        if '#' in fpath:
            fpath, fragment = fpath.split('#', 1)
            lines = fragment
        elif ':' in fpath and not fpath.startswith('http'):
            fpath, lines = fpath.rsplit(':', 1)

        if is_repo_path(fpath):
            gh_url = make_github_file_url(owner, repo, fpath, lines, branch)
            return f'[{label}]({gh_url})'

        return m.group(0)

    text = re.sub(r'\[([^\]\n]+)\]\(([^)\n]*)\)', _repl_link, text)

    # 4. Restore Mermaid blocks
    for idx, block in enumerate(mermaid_blocks):
        text = text.replace(f"<!--MERMAID_BLOCK_{idx}-->", block)

    return text



class DeepWikiUrlParser:
    """Parses and normalizes GitHub or DeepWiki URLs into repository info."""

    @staticmethod
    def parse(input_str: str) -> Tuple[str, str, str, Optional[str]]:
        """
        Parses input string into (owner, repo, deepwiki_base_url, specific_slug).
        
        Supports formats:
          - https://deepwiki.com/microsoft/vscode
          - https://deepwiki.com/microsoft/vscode/1-vs-code-architecture-overview
          - https://github.com/microsoft/vscode
          - git@github.com:microsoft/vscode.git
          - microsoft/vscode
        """
        input_str = input_str.strip()
        
        # Remove git@ prefix if present
        if input_str.startswith("git@github.com:"):
            input_str = input_str.replace("git@github.com:", "https://github.com/")
        if input_str.endswith(".git"):
            input_str = input_str[:-4]

        # Add https scheme if omitted
        if not input_str.startswith("http://") and not input_str.startswith("https://"):
            if "deepwiki.com" in input_str:
                input_str = f"https://{input_str}"
            elif "github.com" in input_str:
                input_str = f"https://{input_str}"
            elif "/" in input_str:
                parts = [p for p in input_str.strip("/").split("/") if p]
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    slug = "/".join(parts[2:]) if len(parts) > 2 else None
                    base_url = f"https://deepwiki.com/{owner}/{repo}"
                    return owner, repo, base_url, slug

        parsed = urlparse(input_str)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

        if len(path_parts) < 2:
            raise ValueError(
                f"Could not parse repository owner and name from '{input_str}'. "
                "Expected format: 'owner/repo', 'https://github.com/owner/repo', or 'https://deepwiki.com/owner/repo'"
            )

        owner = path_parts[0]
        repo = path_parts[1]
        slug = "/".join(path_parts[2:]) if len(path_parts) > 2 else None
        base_url = f"https://deepwiki.com/{owner}/{repo}"

        return owner, repo, base_url, slug


class DeepWikiCrawler:
    """Crawler engine using Crawl4AI to extract complete DeepWiki documentation."""

    def __init__(
        self,
        repo_or_url: str,
        output_dir: str = "./docs",
        concurrency: int = 5,
        delay_between_requests: float = 0.0,
        headless: bool = True,
        verbose: bool = False,
        branch: str = "HEAD",
    ):
        from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
        
        self.owner, self.repo, self.base_url, self.target_slug = DeepWikiUrlParser.parse(repo_or_url)
        self.output_dir = output_dir
        self.concurrency = concurrency
        self.delay_between_requests = delay_between_requests
        self.headless = headless
        self.verbose = verbose
        self.branch = branch

        self.browser_config = BrowserConfig(
            headless=self.headless,
            verbose=self.verbose,
            use_managed_browser=False
        )
        self.run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=5,
            delay_before_return_html=0.5,
        )

    def _extract_rsc_payload(self, html: str) -> str:
        """Extracts and unescapes the Next.js React Server Components (RSC) payload."""
        chunks = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html, re.DOTALL)
        if not chunks:
            return ""

        full_payload = ""
        for chunk in chunks:
            try:
                full_payload += json.loads(f'"{chunk}"')
            except Exception:
                full_payload += chunk

        return full_payload

    def _parse_rsc_chapters(self, payload: str) -> List[CrawledPage]:
        """
        Parses all chapters, page plans, and text chunks directly from the RSC stream.
        This captures 100% of the raw Markdown, including all Mermaid diagrams and tables.
        """
        if not payload:
            return []

        # 1. Find all page plans: {"page_plan":{"id":"...","title":"..."},"content":"$<hex_id>"}
        page_plans_raw = re.findall(r'\{\"page_plan\":(\{[^{}]*\}),\"content\":\"\$([0-9a-f]+)\"\}', payload)
        if not page_plans_raw:
            return []

        # 2. Extract all T-chunks by finding `<hex_id>:T<hex_len>,<text>`
        chunk_pattern = re.compile(r'([0-9a-f]+):T([0-9a-f]+),', re.DOTALL)
        chunks = {}
        for m in chunk_pattern.finditer(payload):
            c_id = m.group(1)
            hex_len = int(m.group(2), 16)
            start_pos = m.end()
            end_pos = start_pos + hex_len
            chunks[c_id] = payload[start_pos:end_pos]

        results: List[CrawledPage] = []
        seen_ids = set()

        for idx, (plan_json_str, content_ref) in enumerate(page_plans_raw):
            try:
                plan = json.loads(plan_json_str)
            except Exception:
                continue

            pid = str(plan.get("id", idx + 1))
            title = plan.get("title", f"Chapter {pid}")

            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            raw_md = chunks.get(content_ref, "")

            # If the chunk wasn't in the root payload map, see if raw_md is elsewhere in payload
            if not raw_md:
                h_pattern = re.compile(rf'(?:^|\n)# {re.escape(title)}[\s\S]*?(?=(?:\n# |\Z))')
                h_match = h_pattern.search(payload)
                if h_match:
                    raw_md = h_match.group(0).strip()

            # Sanitize and validate all Mermaid diagrams
            sanitized_md = sanitize_all_mermaids_in_markdown(raw_md)
            # Convert source file references and line citations to direct GitHub URLs
            sanitized_md = convert_markdown_links_to_github(sanitized_md, self.owner, self.repo, self.branch)
            mermaids = re.findall(r"```mermaid[\s\S]*?```", sanitized_md)
            
            clean_title_slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
            slug = f"{pid}-{clean_title_slug}"
            page_url = f"https://deepwiki.com/{self.owner}/{self.repo}/{slug}"

            meta = WikiPageMeta(
                index=len(results) + 1,
                title=title,
                url=page_url,
                slug=slug,
                chapter_num=pid,
            )

            char_count = len(sanitized_md)
            word_count = len(sanitized_md.split()) if sanitized_md else 0

            results.append(
                CrawledPage(
                    meta=meta,
                    markdown=sanitized_md,
                    success=bool(sanitized_md.strip()),
                    status_code=200,
                    char_count=char_count,
                    word_count=word_count,
                    mermaid_count=len(mermaids),
                )
            )

        return results

    async def fetch_table_of_contents(self, crawler) -> List[WikiPageMeta]:
        """Fetches the repository base page and parses sidebar documentation links."""
        console.print(f"[dim]Fetching repository table of contents from:[/dim] [link={self.base_url}]{self.base_url}[/link]")
        
        result = await crawler.arun(url=self.base_url, config=self.run_config)
        if not result.success:
            raise RuntimeError(f"Failed to load repository page {self.base_url}: {result.error_message}")

        # Try RSC extraction for table of contents first
        rsc_payload = self._extract_rsc_payload(result.html)
        rsc_pages = self._parse_rsc_chapters(rsc_payload)
        if rsc_pages:
            return [p.meta for p in rsc_pages]

        # Fallback to HTML parsing
        soup = BeautifulSoup(result.html, "html.parser")
        link_prefix = f"/{self.owner}/{self.repo}/"
        alt_prefix = f"https://deepwiki.com/{self.owner}/{self.repo}/"
        
        seen_urls = set()
        pages: List[WikiPageMeta] = []
        
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text().strip()
            
            if href.startswith(link_prefix):
                full_url = f"https://deepwiki.com{href}"
                slug = href[len(link_prefix):]
            elif href.startswith(alt_prefix):
                full_url = href
                slug = href[len(alt_prefix):]
            else:
                continue

            if full_url in seen_urls or not slug:
                continue
            
            seen_urls.add(full_url)
            chapter_match = re.match(r"^(\d+(?:\.\d+)*)[-_]", slug)
            chapter_num = chapter_match.group(1) if chapter_match else None
            
            if not title:
                title = slug.replace("-", " ").replace("_", " ").title()

            pages.append(
                WikiPageMeta(
                    index=len(pages) + 1,
                    title=title,
                    url=full_url,
                    slug=slug,
                    chapter_num=chapter_num,
                )
            )

        return pages

    async def crawl(
        self,
        max_pages: Optional[int] = None,
        specific_urls: Optional[List[str]] = None,
    ) -> List[CrawledPage]:
        """Executes the crawl process across documentation pages."""
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_dispatcher import SemaphoreDispatcher, RateLimiter

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            console.print(f"[dim]Connecting to:[/dim] [link={self.base_url}]{self.base_url}[/link]")
            
            # Fetch root page
            root_result = await crawler.arun(url=self.base_url, config=self.run_config)
            if not root_result.success:
                raise RuntimeError(f"Failed to fetch {self.base_url}: {root_result.error_message}")

            # 1. Attempt High-Fidelity RSC Extraction (preserves all Mermaid diagrams & complete text)
            rsc_payload = self._extract_rsc_payload(root_result.html)
            crawled_pages = self._parse_rsc_chapters(rsc_payload)

            missing_chunks = [p for p in crawled_pages if not p.markdown.strip()]
            
            if crawled_pages and not missing_chunks:
                # All pages extracted with 100% fidelity directly from root payload!
                if self.target_slug:
                    matched = [p for p in crawled_pages if self.target_slug in p.meta.slug or self.target_slug in p.meta.url]
                    if matched:
                        crawled_pages = matched

                if max_pages and max_pages > 0:
                    crawled_pages = crawled_pages[:max_pages]

                console.print(f"[green]Discovered and extracted all [bold]{len(crawled_pages)}[/bold] documentation chapters.[/green]")
                return crawled_pages

            # 2. Fallback / Hybrid: Crawl individual pages if necessary
            if specific_urls:
                pages_to_crawl = [
                    WikiPageMeta(
                        index=idx + 1,
                        title=url.split("/")[-1].replace("-", " ").title(),
                        url=url,
                        slug=url.split("/")[-1],
                    )
                    for idx, url in enumerate(specific_urls)
                ]
            elif crawled_pages:
                pages_to_crawl = [p.meta for p in crawled_pages]
            else:
                pages_to_crawl = await self.fetch_table_of_contents(crawler)

            if not pages_to_crawl:
                console.print(
                    f"[yellow]Warning:[/yellow] No documentation pages found for [bold]{self.owner}/{self.repo}[/bold]. "
                    f"Please verify that this repository is indexed on DeepWiki (visit {self.base_url})."
                )
                return []

            if self.target_slug:
                matched = [p for p in pages_to_crawl if self.target_slug in p.slug or self.target_slug in p.url]
                if matched:
                    pages_to_crawl = matched

            if max_pages and max_pages > 0:
                pages_to_crawl = pages_to_crawl[:max_pages]

            total_pages = len(pages_to_crawl)
            console.print(f"[green]Crawling [bold]{total_pages}[/bold] documentation pages with {self.concurrency} workers...[/green]")

            rate_limiter = (
                RateLimiter(base_delay=(self.delay_between_requests, self.delay_between_requests))
                if self.delay_between_requests > 0
                else None
            )
            dispatcher = SemaphoreDispatcher(
                max_session_permit=self.concurrency,
                rate_limiter=rate_limiter,
            )

            urls = [p.url for p in pages_to_crawl]
            meta_by_url = {p.url: p for p in pages_to_crawl}
            final_pages: List[CrawledPage] = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                crawl_task = progress.add_task(f"[bold cyan]Crawling {self.owner}/{self.repo}...", total=total_pages)

                raw_results = await crawler.arun_many(
                    urls=urls,
                    config=self.run_config,
                    dispatcher=dispatcher,
                )

                for r in raw_results:
                    meta = meta_by_url.get(r.url)
                    if not meta:
                        for p in pages_to_crawl:
                            if p.slug in r.url:
                                meta = p
                                break
                        if not meta:
                            meta = WikiPageMeta(
                                index=len(final_pages) + 1,
                                title=r.url.split("/")[-1],
                                url=r.url,
                                slug=r.url.split("/")[-1],
                            )

                    # Extract markdown from individual page RSC stream first (to capture Mermaid)
                    page_rsc = self._extract_rsc_payload(r.html)
                    page_extracted = self._parse_rsc_chapters(page_rsc)
                    
                    md_content = ""
                    if page_extracted:
                        matched_ch = next((ch for ch in page_extracted if ch.meta.slug == meta.slug or ch.meta.title == meta.title), page_extracted[0])
                        md_content = matched_ch.markdown

                    # Fallback to Crawl4AI markdown
                    if not md_content.strip() and r.markdown:
                        md_content = r.markdown.raw_markdown if hasattr(r.markdown, "raw_markdown") else str(r.markdown)

                    # Fallback to DOM BeautifulSoup
                    if not md_content.strip() and r.html:
                        soup = BeautifulSoup(r.html, "html.parser")
                        prose = soup.find("div", class_=re.compile(r"prose"))
                        if prose:
                            md_content = prose.get_text()

                    # Sanitize Mermaid syntax
                    sanitized_md = sanitize_all_mermaids_in_markdown(md_content)
                    # Convert source file references and line citations to direct GitHub URLs
                    sanitized_md = convert_markdown_links_to_github(sanitized_md, self.owner, self.repo, self.branch)
                    mermaids = re.findall(r"```mermaid[\s\S]*?```", sanitized_md)
                    char_count = len(sanitized_md)
                    word_count = len(sanitized_md.split()) if sanitized_md else 0

                    final_pages.append(
                        CrawledPage(
                            meta=meta,
                            markdown=sanitized_md,
                            success=r.success and bool(sanitized_md.strip()),
                            status_code=r.status_code,
                            error=r.error_message if not r.success else None,
                            char_count=char_count,
                            word_count=word_count,
                            mermaid_count=len(mermaids),
                        )
                    )
                    progress.advance(crawl_task)

            final_pages.sort(key=lambda p: p.meta.index)
            return final_pages

    def save(
        self,
        crawled_pages: List[CrawledPage],
        export_format: str = "split",
    ) -> Dict[str, Any]:
        """
        Saves crawled documentation into desired format:
          - 'split': individual .md files per chapter + table of contents
          - 'combined': a single monolithic markdown file
          - 'json': a structured JSON file with all pages and metadata
          - 'all': writes all of the above
        """
        repo_dir_name = f"{self.owner}_{self.repo}".replace("-", "_")
        target_dir = os.path.join(self.output_dir, repo_dir_name)
        os.makedirs(target_dir, exist_ok=True)

        saved_files = []

        # 1. Save Split Markdown files
        if export_format in ("all", "split"):
            split_dir = os.path.join(target_dir, "chapters")
            os.makedirs(split_dir, exist_ok=True)

            # Generate Table of Contents (00_INDEX.md)
            toc_lines = [
                f"# {self.owner}/{self.repo} Documentation",
                f"",
                f"> Automatically crawled from DeepWiki: [{self.base_url}]({self.base_url})",
                f"> Total Chapters: {len(crawled_pages)}",
                f"",
                f"## Table of Contents",
                f"",
            ]

            for page in crawled_pages:
                idx_str = f"{page.meta.index:02d}"
                clean_slug = re.sub(r"[^\w\-.]", "_", page.meta.slug)
                filename = f"{idx_str}_{clean_slug}.md"
                file_path = os.path.join(split_dir, filename)

                file_content = [
                    "---",
                    f"title: \"{page.meta.title}\"",
                    f"chapter: {page.meta.index}",
                    f"source_url: \"{page.meta.url}\"",
                    f"word_count: {page.word_count}",
                    f"mermaid_diagrams: {page.mermaid_count}",
                    "---",
                    "",
                    page.markdown,
                ]

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(file_content))
                saved_files.append(file_path)

                rel_path = f"chapters/{filename}"
                toc_lines.append(f"- [{page.meta.title}]({rel_path})")

            index_path = os.path.join(target_dir, "00_INDEX.md")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("\n".join(toc_lines))
            saved_files.append(index_path)

        # 2. Save Single Combined Markdown file
        if export_format in ("all", "combined"):
            combined_path = os.path.join(target_dir, f"{repo_dir_name}_full.md")
            combined_lines = [
                f"# {self.owner}/{self.repo} - Complete Documentation",
                f"",
                f"> **Repository:** https://github.com/{self.owner}/{self.repo}",
                f"> **Source:** [{self.base_url}]({self.base_url})",
                f"> **Total Chapters:** {len(crawled_pages)}",
                f"",
                "---",
                "",
                "## Table of Contents",
                "",
            ]

            for page in crawled_pages:
                anchor = re.sub(r"[^\w\- ]", "", page.meta.title).lower().replace(" ", "-")
                combined_lines.append(f"- [{page.meta.title}](#{anchor})")

            combined_lines.append("\n---\n")

            for page in crawled_pages:
                combined_lines.append(f"<!-- Chapter {page.meta.index}: {page.meta.title} -->")
                combined_lines.append(f"<!-- Source: {page.meta.url} -->\n")
                combined_lines.append(page.markdown)
                combined_lines.append("\n\n---\n")

            with open(combined_path, "w", encoding="utf-8") as f:
                f.write("\n".join(combined_lines))
            saved_files.append(combined_path)

        # 3. Save Structured JSON dataset
        if export_format in ("all", "json"):
            json_path = os.path.join(target_dir, f"{repo_dir_name}_docs.json")
            data = {
                "repository": f"{self.owner}/{self.repo}",
                "github_url": f"https://github.com/{self.owner}/{self.repo}",
                "deepwiki_url": self.base_url,
                "total_pages": len(crawled_pages),
                "total_mermaid_diagrams": sum(p.mermaid_count for p in crawled_pages),
                "pages": [
                    {
                        "index": p.meta.index,
                        "title": p.meta.title,
                        "slug": p.meta.slug,
                        "url": p.meta.url,
                        "chapter_num": p.meta.chapter_num,
                        "word_count": p.word_count,
                        "char_count": p.char_count,
                        "mermaid_count": p.mermaid_count,
                        "markdown": p.markdown,
                    }
                    for p in crawled_pages
                ],
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            saved_files.append(json_path)

        return {
            "target_dir": target_dir,
            "saved_files": saved_files,
            "total_pages": len(crawled_pages),
            "total_mermaids": sum(p.mermaid_count for p in crawled_pages),
        }


def print_summary_table(pages: List[CrawledPage]):
    """Displays a formatted Rich summary table of all crawled pages."""
    table = Table(title="Crawled Documentation Summary", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Title", style="bold cyan", min_width=30)
    table.add_column("Words", justify="right", style="green")
    table.add_column("Mermaid", justify="center", style="yellow")
    table.add_column("Status", justify="center")

    total_words = 0
    total_mermaids = 0
    success_count = 0

    rows_to_show = pages if len(pages) <= 25 else pages[:20] + pages[-5:]

    for idx, page in enumerate(rows_to_show):
        if len(pages) > 25 and idx == 20:
            table.add_row("...", f"[dim]... {len(pages) - 25} more chapters ...[/dim]", "...", "...", "...")

        status = "[green][OK][/green]" if page.success else f"[red][FAIL] ({page.error or 'Empty'})[/red]"
        mermaid_display = f"{page.mermaid_count} diagram(s)" if page.mermaid_count > 0 else "[dim]-[/dim]"
        table.add_row(
            str(page.meta.index),
            page.meta.title[:45] + ("..." if len(page.meta.title) > 45 else ""),
            f"{page.word_count:,}",
            mermaid_display,
            status,
        )

    for page in pages:
        if page.success:
            total_words += page.word_count
            total_mermaids += page.mermaid_count
            success_count += 1

    console.print(table)
    console.print(
        Panel.fit(
            f"[bold green]Successfully extracted {success_count}/{len(pages)} chapters[/bold green] | "
            f"[bold cyan]Total Words: {total_words:,}[/bold cyan] | "
            f"[bold yellow]Mermaid Diagrams: {total_mermaids}[/bold yellow]",
            title="Extraction Complete",
            border_style="green",
        )
    )


async def main_async(args):
    """Main asynchronous execution flow."""
    banner = """
=================================================================
                     DeepWiki Doc Crawler                        
      AI-Powered Documentation Extraction using Crawl4AI       
=================================================================
"""
    console.print(banner, style="bold blue")

    try:
        crawler = DeepWikiCrawler(
            repo_or_url=args.url,
            output_dir=args.output,
            concurrency=args.concurrency,
            delay_between_requests=args.delay,
            headless=not args.headful,
            verbose=args.verbose,
            branch=args.branch,
        )
    except Exception as e:
        console.print(f"[red]Error parsing URL:[/red] {e}")
        sys.exit(1)

    console.print(
        Panel.fit(
            f"[bold]Target Repository:[/bold] [green]{crawler.owner}/{crawler.repo}[/green]\n"
            f"[bold]DeepWiki URL:[/bold] [link={crawler.base_url}]{crawler.base_url}[/link]\n"
            f"[bold]GitHub Branch:[/bold] [yellow]{args.branch}[/yellow]\n"
            f"[bold]Output Directory:[/bold] {args.output}\n"
            f"[bold]Concurrency:[/bold] {args.concurrency} workers | [bold]Format:[/bold] {args.format}",
            title="Configuration",
            border_style="blue",
        )
    )

    # If TOC inspection only is requested
    if args.toc_only:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(config=crawler.browser_config) as client:
            pages = await crawler.fetch_table_of_contents(client)
            table = Table(title=f"Table of Contents for {crawler.owner}/{crawler.repo}", show_header=True)
            table.add_column("#", style="dim", width=4)
            table.add_column("Chapter Title", style="bold cyan")
            table.add_column("URL", style="dim")

            for p in pages:
                table.add_row(str(p.index), p.title, p.url)
            console.print(table)
            console.print(f"[green]Total {len(pages)} chapters discovered.[/green]")
            return

    # Crawl / Extract
    pages = await crawler.crawl(max_pages=args.max_pages)

    if not pages:
        console.print("[red]No documentation pages were extracted.[/red]")
        return

    # Display summary
    print_summary_table(pages)

    # Save to disk
    result = crawler.save(pages, export_format=args.format)
    console.print(f"\n[bold green]Exported documentation to:[/bold green] [bold cyan]{result['target_dir']}[/bold cyan]")
    for path in result["saved_files"][:10]:
        console.print(f"  [dim]-[/dim] {os.path.basename(path)}")
    if len(result["saved_files"]) > 10:
        console.print(f"  [dim]... and {len(result['saved_files']) - 10} more files.[/dim]")


def parse_args():
    parser = argparse.ArgumentParser(
        description="DeepWiki Documentation Crawler using Crawl4AI. Extract clean docs from any GitHub repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl all VS Code documentation from GitHub link (all 75 chapters + all Mermaid diagrams)
  deepwiki https://github.com/microsoft/vscode

  # Or using shorthand repository slug
  deepwiki microsoft/vscode

  # Crawl with 10 parallel browser workers
  deepwiki microsoft/vscode -c 10

  # Export as a single combined markdown file for LLMs & RAG
  deepwiki microsoft/vscode -f combined -o ./knowledge_base

  # Crawl only the first 5 pages as a quick test
  deepwiki fastapi/fastapi --max-pages 5

  # Inspect Table of Contents only without crawling content
  deepwiki microsoft/vscode --toc-only
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="deepwiki-cli 1.0.0",
    )
    parser.add_argument(
        "url",
        help="GitHub URL (e.g. https://github.com/microsoft/vscode), DeepWiki URL, or repository name (e.g. microsoft/vscode)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./docs",
        help="Directory where crawled documentation will be saved (default: ./docs)",
    )
    parser.add_argument(
        "-b",
        "--branch",
        default="HEAD",
        help="GitHub branch, tag, or commit ref for source file links (default: HEAD)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["all", "split", "combined", "json"],
        default="split",
        help="Output format: 'split' (markdown files per chapter), 'combined' (single .md file), 'json', or 'all' (default: split)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent crawler workers (default: 5)",
    )
    parser.add_argument(
        "-m",
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to crawl (useful for quick testing)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between requests for polite crawling (default: 0.0)",
    )
    parser.add_argument(
        "--toc-only",
        action="store_true",
        help="Fetch and display Table of Contents only without crawling page contents",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser in headful mode (visible browser window)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose crawl4ai logging",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
