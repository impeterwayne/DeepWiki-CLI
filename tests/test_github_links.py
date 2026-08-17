"""
Regression and unit tests for GitHub link and citation converter.

Ensures that source file references, relative file paths, and in-text line citations
in DeepWiki markdown are cleanly converted to direct, clickable GitHub URLs.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepwiki_crawler import (
    convert_markdown_links_to_github,
    make_github_file_url,
    is_repo_path,
    build_chapter_lookup,
    resolve_page_chapter_links,
    WikiPageMeta,
    CrawledPage,
)


class TestGitHubLinkConverter(unittest.TestCase):
    def setUp(self):
        self.owner = "microsoft"
        self.repo = "vscode"

    def test_empty_url_with_line_range(self):
        md = "See [src/vs/code/electron-main/app.ts:58-80]()."
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(
            res,
            "See [src/vs/code/electron-main/app.ts:58-80](https://github.com/microsoft/vscode/blob/HEAD/src/vs/code/electron-main/app.ts#L58-L80)."
        )

    def test_empty_url_with_single_line(self):
        md = "Entry: [src/vs/workbench/browser/web.main.ts:13-13]()."
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(
            res,
            "Entry: [src/vs/workbench/browser/web.main.ts:13-13](https://github.com/microsoft/vscode/blob/HEAD/src/vs/workbench/browser/web.main.ts#L13)."
        )

    def test_empty_url_with_multi_range(self):
        md = "Config: [package.json:25-27, 74-74]()."
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(
            res,
            "Config: [package.json:25-27, 74-74](https://github.com/microsoft/vscode/blob/HEAD/package.json#L25-L27)."
        )

    def test_empty_url_bare_file(self):
        md = "Check [src/vs/base/common/defaultAccount.ts]()."
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(
            res,
            "Check [src/vs/base/common/defaultAccount.ts](https://github.com/microsoft/vscode/blob/HEAD/src/vs/base/common/defaultAccount.ts)."
        )

    def test_backtick_file_with_line_link(self):
        md = "- `src/vs/code/electron-main/app.ts` [58-80]()"
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(
            res,
            "- `src/vs/code/electron-main/app.ts` [58-80](https://github.com/microsoft/vscode/blob/HEAD/src/vs/code/electron-main/app.ts#L58-L80)"
        )

    def test_relevant_source_files_relative_links(self):
        md = (
            "<details>\n"
            "<summary>Relevant source files</summary>\n\n"
            "- [README.md](README.md)\n"
            "- [.npmrc](.npmrc)\n"
            "- [extensions/github-authentication/media/auth.css](extensions/github-authentication/media/auth.css)\n"
            "</details>"
        )
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertIn("https://github.com/microsoft/vscode/blob/HEAD/README.md", res)
        self.assertIn("https://github.com/microsoft/vscode/blob/HEAD/.npmrc", res)
        self.assertIn("https://github.com/microsoft/vscode/blob/HEAD/extensions/github-authentication/media/auth.css", res)

    def test_preserve_anchors(self):
        md = "For details, see [Repository Structure](#1.1)."
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(res, "For details, see [Repository Structure](#1.1).")

    def test_preserve_external_urls(self):
        md = "Visit [DeepWiki](https://deepwiki.com/microsoft/vscode) for more info."
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(res, "Visit [DeepWiki](https://deepwiki.com/microsoft/vscode) for more info.")

    def test_preserve_index_chapter_links(self):
        md = "- [Chapter 1](chapters/01_1-vs-code-architecture-overview.md)"
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(res, "- [Chapter 1](chapters/01_1-vs-code-architecture-overview.md)")

    def test_sources_line_with_multiple_citations(self):
        md = "Sources: [src/vs/workbench/services/auth.ts:93-115](), [src/vs/workbench/api/main.ts:114-132]()"
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
        self.assertEqual(
            res,
            "Sources: [src/vs/workbench/services/auth.ts:93-115](https://github.com/microsoft/vscode/blob/HEAD/src/vs/workbench/services/auth.ts#L93-L115), [src/vs/workbench/api/main.ts:114-132](https://github.com/microsoft/vscode/blob/HEAD/src/vs/workbench/api/main.ts#L114-L132)"
        )

    def test_custom_branch(self):
        md = "[src/index.ts:10-20]()"
        res = convert_markdown_links_to_github(md, "owner", "repo", branch="main")
        self.assertEqual(
            res,
            "[src/index.ts:10-20](https://github.com/owner/repo/blob/main/src/index.ts#L10-L20)"
        )

    def test_extensionless_root_files_with_lines(self):
        md = "Scripts: [gradlew:1-249](), [gradlew:203](), [Makefile:10-20]()."
        res = convert_markdown_links_to_github(md, "skylot", "jadx")
        self.assertEqual(
            res,
            "Scripts: [gradlew:1-249](https://github.com/skylot/jadx/blob/HEAD/gradlew#L1-L249), "
            "[gradlew:203](https://github.com/skylot/jadx/blob/HEAD/gradlew#L203), "
            "[Makefile:10-20](https://github.com/skylot/jadx/blob/HEAD/Makefile#L10-L20)."
        )

    def test_extensionless_root_files_bare(self):
        md = "See [gradlew](gradlew) and [Makefile]()."
        res = convert_markdown_links_to_github(md, "skylot", "jadx")
        self.assertEqual(
            res,
            "See [gradlew](https://github.com/skylot/jadx/blob/HEAD/gradlew) and "
            "[Makefile](https://github.com/skylot/jadx/blob/HEAD/Makefile)."
        )

    def test_contextual_line_citations(self):
        md = (
            "The `NameMapper` class enforces identifier legality. "
            "[jadx-core/src/main/java/jadx/core/deobf/NameMapper.java:12-12](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/core/deobf/NameMapper.java#L12)\n\n"
            "| Method | Purpose |\n"
            "|---|---|\n"
            "| `isReserved(String)` | Checks reserved word [line 77-79]() |\n"
            "| `isValidIdentifier(String)` | Validates identifier [line 81-85]() |\n"
            "| `multiLine()` | Multi range [line 102-132, 150-178]() |\n"
        )
        res = convert_markdown_links_to_github(md, "skylot", "jadx")
        self.assertIn("[line 77-79](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/core/deobf/NameMapper.java#L77-L79)", res)
        self.assertIn("[line 81-85](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/core/deobf/NameMapper.java#L81-L85)", res)
        self.assertIn("[line 102-132, 150-178](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/core/deobf/NameMapper.java#L102-L132)", res)

    def test_jadx_field_and_method_info_aliasing(self):
        md = (
            "Method aliasing in [jadx-core/src/main/java/jadx/core/dex/info/MethodInfo.java:15-204](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/core/dex/info/MethodInfo.java#L15-L204):\n"
            "- **alias**: Deobfuscated name. [line 25, 29]()\n"
            "- **setAlias(String)**: Updates the alias. [line 156-158]()\n"
        )
        res = convert_markdown_links_to_github(md, "skylot", "jadx")
        self.assertIn("[line 25, 29](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/core/dex/info/MethodInfo.java#L25)", res)
        self.assertIn("[line 156-158](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/core/dex/info/MethodInfo.java#L156-L158)", res)

    def test_unwrap_backtick_wrapped_links(self):
        md = "See `[jadx-core/src/main/java/jadx/api/JadxDecompiler.java:59-85](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/api/JadxDecompiler.java#L59-L85)` and `[README.md:14-26]()`."
        res = convert_markdown_links_to_github(md, "skylot", "jadx")
        self.assertNotIn("`[", res)
        self.assertNotIn("]`", res)
        self.assertIn("[jadx-core/src/main/java/jadx/api/JadxDecompiler.java:59-85](https://github.com/skylot/jadx/blob/HEAD/jadx-core/src/main/java/jadx/api/JadxDecompiler.java#L59-L85)", res)
        self.assertIn("[README.md:14-26](https://github.com/skylot/jadx/blob/HEAD/README.md#L14-L26)", res)


class TestChapterLinkResolution(unittest.TestCase):
    def setUp(self):
        self.pages = [
            CrawledPage(
                meta=WikiPageMeta(
                    index=1,
                    title="Overview",
                    url="https://deepwiki.com/skylot/jadx/1-overview",
                    slug="1-overview",
                    chapter_num="1",
                ),
                markdown=(
                    "# Overview\n\n"
                    "## Purpose and Scope\n"
                    "Intro text.\n\n"
                    "For detailed info:\n"
                    "- Installation: see [Getting Started](#1.1)\n"
                    "- Deep dive: see [Architecture Overview](#1.2)\n"
                    "- Build: see [Build System and Distribution](#5)\n"
                    "- Plugin: see [Plugin System](#6)\n"
                    "- Local section: see [Purpose and Scope](#purpose-and-scope)\n"
                ),
                success=True,
            ),
            CrawledPage(
                meta=WikiPageMeta(
                    index=2,
                    title="Getting Started",
                    url="https://deepwiki.com/skylot/jadx/1.1-getting-started",
                    slug="1.1-getting-started",
                    chapter_num="1.1",
                ),
                markdown="# Getting Started\n\nInstall instructions.",
                success=True,
            ),
            CrawledPage(
                meta=WikiPageMeta(
                    index=3,
                    title="Architecture Overview",
                    url="https://deepwiki.com/skylot/jadx/1.2-architecture-overview",
                    slug="1.2-architecture-overview",
                    chapter_num="1.2",
                ),
                markdown="# Architecture Overview\n\nArchitecture details.",
                success=True,
            ),
            CrawledPage(
                meta=WikiPageMeta(
                    index=6,
                    title="Decompilation Pipeline",
                    url="https://deepwiki.com/skylot/jadx/2.2-decompilation-pipeline",
                    slug="2.2-decompilation-pipeline",
                    chapter_num="2.2",
                ),
                markdown=(
                    "# Decompilation Pipeline\n\n"
                    "## SSA Transformation Phase\n"
                    "Details on SSA."
                ),
                success=True,
            ),
            CrawledPage(
                meta=WikiPageMeta(
                    index=24,
                    title="Build System and Distribution",
                    url="https://deepwiki.com/skylot/jadx/5-build-system-and-distribution",
                    slug="5-build-system-and-distribution",
                    chapter_num="5",
                ),
                markdown="# Build System and Distribution\n\nBuild details.",
                success=True,
            ),
            CrawledPage(
                meta=WikiPageMeta(
                    index=29,
                    title="Plugin System",
                    url="https://deepwiki.com/skylot/jadx/6-plugin-system",
                    slug="6-plugin-system",
                    chapter_num="6",
                ),
                markdown="# Plugin System\n\nPlugin details.",
                success=True,
            ),
        ]
        self.chapter_map, self.page_headings = build_chapter_lookup(self.pages, "skylot", "jadx")

    def test_cross_chapter_links_in_overview(self):
        page1 = self.pages[0]
        res = resolve_page_chapter_links(
            page1.markdown,
            page1.meta.index,
            self.chapter_map,
            self.page_headings,
            target_mode="split",
        )
        self.assertIn("[Getting Started](02_1.1-getting-started.md)", res)
        self.assertIn("[Architecture Overview](03_1.2-architecture-overview.md)", res)
        self.assertIn("[Build System and Distribution](24_5-build-system-and-distribution.md)", res)
        self.assertIn("[Plugin System](29_6-plugin-system.md)", res)
        # Local heading on current page remains an in-page anchor
        self.assertIn("[Purpose and Scope](#purpose-and-scope)", res)

    def test_cross_chapter_subheading_link(self):
        md = "For SSA info, see [SSA Transformation Phase](#ssa-transformation-phase)."
        res = resolve_page_chapter_links(
            md,
            1,  # from page 1
            self.chapter_map,
            self.page_headings,
            target_mode="split",
        )
        self.assertEqual(
            res,
            "For SSA info, see [SSA Transformation Phase](06_2.2-decompilation-pipeline.md#ssa-transformation-phase)."
        )

    def test_empty_url_chapter_name_resolution(self):
        md = "Check [Getting Started]() and [Decompilation Pipeline]()."
        res = resolve_page_chapter_links(
            md,
            1,
            self.chapter_map,
            self.page_headings,
            target_mode="split",
        )
        self.assertEqual(
            res,
            "Check [Getting Started](02_1.1-getting-started.md) and [Decompilation Pipeline](06_2.2-decompilation-pipeline.md)."
        )

    def test_combined_mode_resolution(self):
        page1 = self.pages[0]
        res = resolve_page_chapter_links(
            page1.markdown,
            page1.meta.index,
            self.chapter_map,
            self.page_headings,
            target_mode="combined",
        )
        self.assertIn("[Getting Started](#getting-started)", res)
        self.assertIn("[Architecture Overview](#architecture-overview)", res)


if __name__ == "__main__":
    unittest.main()
