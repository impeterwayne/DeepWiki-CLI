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


def clean_node_identifier(label: str) -> str:
    """Generates a clean alphanumeric identifier for a Mermaid node."""
    cleaned = re.sub(r'[\'\"\[\]\{\}\(\)\<\>\:\/\*\.\-\s\$\@\,\=\+\;\#\!\\\|\?]+', '_', label).strip('_')
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"node_{cleaned}"
    return cleaned[:40]


def sanitize_mermaid_block(block: str) -> str:
    """
    Cleans and repairs syntax issues produced by AI-generated Mermaid diagrams:
      1. Anonymous bracket nodes: `["Label"]` -> `NodeID["Label"]`
      2. Nested double/single quotes: `["'Label'"]` -> `NodeID["Label"]`
      3. Unquoted bracket nodes: `[Label]` -> `NodeID["Label"]`
      4. Invalid sequenceDiagram participants: `participant ["Name"]` -> `participant Name as "Name"`
      5. Subgraphs with colons or unescaped characters
      6. Nodes with nested square brackets inside labels: `A["Label [sub]"]` -> `A["Label (sub)"]`
    """
    lines = block.strip().split("\n")
    if not lines:
        return block

    first_line = lines[0].strip()
    is_sequence = first_line.startswith("sequenceDiagram")
    is_graph = first_line.startswith("graph") or first_line.startswith("flowchart")

    cleaned_lines = []

    # Sequence diagrams
    if is_sequence:
        for line in lines:
            l = line
            # participant ["Name"] -> participant Name as "Name"
            m_part = re.search(r'participant\s+\[\"([^\"]+)\"\]', l)
            if m_part:
                raw_name = m_part.group(1)
                p_id = clean_node_identifier(raw_name)
                l = re.sub(r'participant\s+\[\"[^\"]+\"\]', f'participant {p_id} as "{raw_name}"', l)
            
            # ["Name"] in arrows -> Name
            l = re.sub(r'\[\"([^\"]+)\"\]', lambda m: clean_node_identifier(m.group(1)), l)
            cleaned_lines.append(l)
        return "\n".join(cleaned_lines)

    if not is_graph:
        return block

    for line in lines:
        l = line

        # 1. Subgraph cleaning: `subgraph "Name"` or `subgraph "ID" ["Label"]`
        m_sub = re.match(r'^(\s*subgraph\s+)\"([^\"]+)\"(\s*\[\"?([^\"]*)\"?\])?\s*$', l)
        if m_sub:
            indent = m_sub.group(1)
            raw_title = m_sub.group(2)
            explicit_label = m_sub.group(4) or raw_title
            sub_id = clean_node_identifier(raw_title)
            l = f'{indent}{sub_id} ["{explicit_label}"]'
            cleaned_lines.append(l)
            continue

        # 2. Anonymous bracket nodes with quotes: `["Label"]` or `["'Label'"]`
        def replace_quoted_anonymous(match):
            inner = match.group(1).strip()
            if (inner.startswith("'") and inner.endswith("'")) or (inner.startswith('"') and inner.endswith('"')):
                inner = inner[1:-1].strip()
            clean_label = inner.replace("[", "(").replace("]", ")").replace('"', "'")
            node_id = clean_node_identifier(clean_label)
            return f'{node_id}["{clean_label}"]'

        l = re.sub(r'(?<![a-zA-Z0-9_\-\$])\[\"([^\"]+)\"\]', replace_quoted_anonymous, l)

        # 3. Anonymous unquoted bracket nodes: `[Label]` or `[EnvCheck{"Label"}]`
        def replace_unquoted_anonymous(match):
            inner = match.group(1).strip()
            if '{"' in inner or "{\'" in inner:
                m_shape = re.match(r'^([a-zA-Z0-9_]+)\{\"?([^\"]+)\"?\}$', inner)
                if m_shape:
                    s_id = m_shape.group(1)
                    s_lbl = m_shape.group(2).replace('"', "'")
                    return f'{s_id}{{"{s_lbl}"}}'
            if re.match(r'^[a-zA-Z0-9_\s\.\-\/\:]+$', inner):
                clean_label = inner.replace('"', "'")
                node_id = clean_node_identifier(clean_label)
                return f'{node_id}["{clean_label}"]'
            return match.group(0)

        l = re.sub(r'(?<![a-zA-Z0-9_\-\$])\[([a-zA-Z0-9_\s\.\-\/\:\{\}\"\']+)\](?!\s*[\(\[\{\<\>])', replace_unquoted_anonymous, l)

        cleaned_lines.append(l)

    return "\n".join(cleaned_lines)


def sanitize_all_mermaids_in_markdown(md_text: str) -> str:
    """Finds all Mermaid code blocks in Markdown and cleans their syntax."""
    def _repl(match):
        raw_code = match.group(1)
        fixed_code = sanitize_mermaid_block(raw_code)
        return f"```mermaid\n{fixed_code.strip()}\n```"

    return re.sub(r'```mermaid([\s\S]*?)```', _repl, md_text)


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
    ):
        from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
        
        self.owner, self.repo, self.base_url, self.target_slug = DeepWikiUrlParser.parse(repo_or_url)
        self.output_dir = output_dir
        self.concurrency = concurrency
        self.delay_between_requests = delay_between_requests
        self.headless = headless
        self.verbose = verbose

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
        )
    except Exception as e:
        console.print(f"[red]Error parsing URL:[/red] {e}")
        sys.exit(1)

    console.print(
        Panel.fit(
            f"[bold]Target Repository:[/bold] [green]{crawler.owner}/{crawler.repo}[/green]\n"
            f"[bold]DeepWiki URL:[/bold] [link={crawler.base_url}]{crawler.base_url}[/link]\n"
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
