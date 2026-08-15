# DeepWiki CLI

Extract complete repository wikis and documentation from DeepWiki or GitHub into clean Markdown, JSON, and Mermaid diagrams with a single command.

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Crawl4AI](https://img.shields.io/badge/crawler-Crawl4AI-orange.svg)](https://github.com/unclecode/crawl4ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Key Features

- **Any Repository Input**: Accepts GitHub URLs (`https://github.com/owner/repo`), shorthand slugs (`owner/repo`), or DeepWiki URLs (`https://deepwiki.com/owner/repo`).
- **High-Throughput Parallel Engine**: Powered by `Crawl4AI` with async browser orchestration, rate-limiting control, and hybrid streaming fallbacks.
- **Multi-Format Exports (Ready for AI & RAG)**:
  - **`combined`**: A monolithic single Markdown file with clickable TOC anchors (ideal for Google NotebookLM, Claude Projects, and ChatGPT).
  - **`split`**: Individual chapter Markdown files with structured YAML frontmatter + `00_INDEX.md` index.
  - **`json`**: Structured dataset containing repository metadata, chapter word counts, diagram counts, and raw markdown for Vector DB embeddings & RAG.
  - **`all`**: Generates all of the above formats (`combined`, `split`, and `json`) in a single execution.

---

## Installation

### Option 1: 1-Command Install

```bash
pip install -e .
playwright install chromium
```

### Option 2: 1-Click Automated Scripts

- **Windows PowerShell**: `.\install.ps1`
- **Windows CMD**: `install.bat`
- **Linux / macOS**: `chmod +x install.sh && ./install.sh`

---

## Quick Start (CLI)

Once installed, use the `deepwiki` command directly from any terminal window:

```bash
# 1. Crawl all documentation for a GitHub repository
deepwiki https://github.com/microsoft/vscode

# 2. Or using repository slug
deepwiki microsoft/vscode

# 3. High-speed parallel crawl (e.g. 10 workers)
deepwiki microsoft/vscode -c 10

# 4. Export as a single combined file for LLMs & RAG
deepwiki microsoft/vscode -f combined -o ./knowledge_base

# 5. Quick test crawl (e.g. first 5 pages)
deepwiki fastapi/fastapi --max-pages 5

# 6. Inspect Table of Contents only without downloading content
deepwiki microsoft/vscode --toc-only
```

---

## CLI Options Reference

```text
usage: deepwiki [-h] [--version] [-o OUTPUT] [-f {all,split,combined,json}]
                [-c CONCURRENCY] [-m MAX_PAGES] [--delay DELAY] [--toc-only]
                [--headful] [-v]
                url
```

| Argument | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `url` | - | *Required* | GitHub URL (`https://github.com/owner/repo`), DeepWiki URL, or `owner/repo` |
| `--output` | `-o` | `./docs` | Destination directory for saved files |
| `--format` | `-f` | `split` | Output format: `split`, `combined`, `json`, or `all` |
| `--concurrency` | `-c` | `5` | Number of parallel browser workers |
| `--max-pages` | `-m` | `None` | Limit number of chapters to scrape (default: scrape ALL chapters) |
| `--delay` | - | `0.0` | Delay in seconds between requests for polite crawling |
| `--toc-only` | - | `False` | Discover and print Table of Contents without scraping pages |
| `--headful` | - | `False` | Run browser in visible window |
| `--verbose` | `-v` | `False` | Enable verbose crawl4ai logging |
| `--version` | - | | Show program's version number and exit |

---

## Output Folder Structure

When you crawl a repository like `microsoft/vscode`, the output directory looks like this:

```text
docs/
└── microsoft_vscode/
    ├── 00_INDEX.md                           # Master Table of Contents with relative links
    ├── microsoft_vscode_full.md              # Single combined Markdown file with all Mermaid diagrams
    ├── microsoft_vscode_docs.json            # Structured JSON dataset for RAG pipelines
    └── chapters/                             # Individual chapter markdown files
        ├── 01_1-vs-code-architecture-overview.md
        ├── 02_1.1-repository-structure-and-build-system.md
        ├── 03_1.2-core-architectural-layers.md
        └── ... (all 75+ chapters)
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.