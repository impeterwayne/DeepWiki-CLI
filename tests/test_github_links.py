"""
Regression and unit tests for GitHub link and citation converter.

Ensures that source file references, relative file paths, and in-text line citations
in DeepWiki markdown are cleanly converted to direct, clickable GitHub URLs.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepwiki_crawler import convert_markdown_links_to_github, make_github_file_url, is_repo_path


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
            "- [.npmrc](.npmrc)\n"
            "- [extensions/github-authentication/media/auth.css](extensions/github-authentication/media/auth.css)\n"
            "</details>"
        )
        res = convert_markdown_links_to_github(md, self.owner, self.repo)
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


if __name__ == "__main__":
    unittest.main()
