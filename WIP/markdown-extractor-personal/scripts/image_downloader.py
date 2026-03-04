#!/usr/bin/env python3
"""
image_downloader.py

Processes a markdown file, downloads all remote images to a local
_ref/ folder alongside the markdown file, and rewrites all
image references in-place to use local relative paths.

Usage:
    python image_downloader.py <path-to-markdown-file>

Exit codes:
    0 — all images processed (or none found)
    1 — one or more image downloads failed
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib import parse, request


# ---------------------------------------------------------------------------
# Data objects
# ---------------------------------------------------------------------------


@dataclass
class ImageReference:
    """A single image reference found in the markdown document."""

    original_text: str  # Full matched string, e.g. ![alt](url) or <img src="url">
    url: str            # Raw URL or path extracted from the reference
    alt_text: str = "" # Alt text (markdown syntax only)
    is_html: bool = False  # True when found via <img src="...">


@dataclass
class DownloadResult:
    """Outcome of processing one ImageReference."""

    reference: ImageReference
    local_path: Optional[Path] = None
    success: bool = False
    skipped: bool = False
    error: str = ""


@dataclass
class ProcessingReport:
    """Accumulates statistics and per-image results for the full run."""

    total_found: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    results: list[DownloadResult] = field(default_factory=list)

    def print_summary(self) -> None:
        print("\n--- Image Processing Summary ---")
        print(f"  Found      : {self.total_found}")
        print(f"  Downloaded : {self.downloaded}")
        print(f"  Skipped    : {self.skipped}  (local paths / data URIs)")
        print(f"  Failed     : {self.failed}")
        if self.failed:
            print("\n  Failed downloads:")
            for r in self.results:
                if not r.success and not r.skipped:
                    print(f"    - {r.reference.url}")
                    print(f"      {r.error}")


# ---------------------------------------------------------------------------
# MarkdownImageParser
# Responsibility: find all image references in raw markdown text.
# ---------------------------------------------------------------------------


class MarkdownImageParser:
    """
    Extracts ImageReference objects from markdown content.

    Handles two syntaxes:
      - Markdown : ![alt text](url)  or  ![alt](url "optional title")
      - HTML     : <img src="url" ...>  or  <img src='url' ...>
    """

    _MD_IMAGE = re.compile(
        r'!\[(?P<alt>[^\]]*)\]'      # ![alt]
        r'\((?P<url>[^)\s"\']+)'     # (url   — stops at whitespace, quote, or )
        r'(?:\s+"[^"]*")?\)',        # optional title, then )
    )

    _HTML_IMAGE = re.compile(
        r'<img\b[^>]*\bsrc=["\'](?P<url>[^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )

    def parse(self, content: str) -> list[ImageReference]:
        """Return all unique image references found in *content*."""
        refs: list[ImageReference] = []
        seen: set[str] = set()

        for match in self._MD_IMAGE.finditer(content):
            url = match.group("url")
            if url not in seen:
                refs.append(ImageReference(
                    original_text=match.group(0),
                    url=url,
                    alt_text=match.group("alt"),
                    is_html=False,
                ))
                seen.add(url)

        for match in self._HTML_IMAGE.finditer(content):
            url = match.group("url")
            if url not in seen:
                refs.append(ImageReference(
                    original_text=match.group(0),
                    url=url,
                    is_html=True,
                ))
                seen.add(url)

        return refs


# ---------------------------------------------------------------------------
# AssetStore
# Responsibility: manage the local assets directory and filename allocation.
# ---------------------------------------------------------------------------


class AssetStore:
    """
    Manages the ``_ref/`` directory adjacent to the markdown file.

    Ensures unique filenames by appending a counter suffix on collision.
    """

    def __init__(self, markdown_path: Path) -> None:
        self._assets_dir = markdown_path.parent / "_ref"
        self._assets_dir.mkdir(parents=True, exist_ok=True)
        self._allocated: set[str] = set()

    @property
    def directory(self) -> Path:
        return self._assets_dir

    def allocate(self, url: str) -> Path:
        """
        Reserve a unique local filename derived from *url* and return its
        full path inside the assets directory.
        """
        parsed = parse.urlparse(url)
        raw_name = Path(parsed.path).name or "image"
        stem = Path(raw_name).stem or "image"
        suffix = Path(raw_name).suffix or ".jpg"

        candidate = raw_name
        counter = 1
        while candidate in self._allocated or (self._assets_dir / candidate).exists():
            candidate = f"{stem}_{counter}{suffix}"
            counter += 1

        self._allocated.add(candidate)
        return self._assets_dir / candidate

    def relative_to_note(self, asset_path: Path, markdown_path: Path) -> str:
        """
        Return *asset_path* as a POSIX-style relative path from the
        markdown file's parent directory.
        """
        return asset_path.relative_to(markdown_path.parent).as_posix()


# ---------------------------------------------------------------------------
# ImageDownloader
# Responsibility: fetch one remote image and write it to disk.
# ---------------------------------------------------------------------------


class ImageDownloader:
    """
    Downloads a single remote image URL to a local destination path.

    Uses only ``urllib`` from the standard library — no external dependencies.
    """

    TIMEOUT = 15  # seconds
    HEADERS = {"User-Agent": "markdown-extractor-personal/1.0"}

    def is_remote(self, url: str) -> bool:
        """True when *url* points to an http(s) resource."""
        return url.startswith(("http://", "https://"))

    def is_data_uri(self, url: str) -> bool:
        """True when *url* is an inline data URI."""
        return url.startswith("data:")

    def fetch(self, url: str, destination: Path) -> None:
        """
        Download *url* and write its content to *destination*.

        Raises ``urllib.error.URLError`` or ``OSError`` on failure.
        """
        req = request.Request(url, headers=self.HEADERS)
        with request.urlopen(req, timeout=self.TIMEOUT) as response:
            destination.write_bytes(response.read())


# ---------------------------------------------------------------------------
# LinkRewriter
# Responsibility: rewrite image URLs in markdown text using download results.
# ---------------------------------------------------------------------------


class LinkRewriter:
    """
    Replaces remote image URLs in markdown content with local relative paths.

    For failed downloads, the original reference is preserved and annotated
    with an inline ``<!-- download-failed -->`` comment.
    """

    def rewrite(
        self,
        content: str,
        results: list[DownloadResult],
        asset_store: AssetStore,
        markdown_path: Path,
    ) -> str:
        """Return *content* with all image URLs rewritten according to *results*."""
        for result in results:
            if result.skipped:
                continue

            ref = result.reference
            if result.success and result.local_path:
                local_rel = asset_store.relative_to_note(result.local_path, markdown_path)
                new_text = ref.original_text.replace(ref.url, local_rel)
            else:
                new_text = ref.original_text + "<!-- download-failed -->"

            content = content.replace(ref.original_text, new_text, 1)

        return content


# ---------------------------------------------------------------------------
# MarkdownImageProcessor
# Responsibility: orchestrate the full parse → download → rewrite → save pipeline.
# ---------------------------------------------------------------------------


class MarkdownImageProcessor:
    """
    Coordinates all concerns to process a single markdown file end-to-end.

    Pipeline:
      1. Parse the file for image references.
      2. Download each remote image into the local asset store.
      3. Rewrite links in the content.
      4. Overwrite the markdown file with updated content.
      5. Return a ProcessingReport with full statistics.
    """

    def __init__(self, markdown_path: Path) -> None:
        self._path = markdown_path
        self._parser = MarkdownImageParser()
        self._downloader = ImageDownloader()
        self._asset_store = AssetStore(markdown_path)
        self._rewriter = LinkRewriter()

    def run(self) -> ProcessingReport:
        """Execute the full pipeline and return the processing report."""
        report = ProcessingReport()

        content = self._path.read_text(encoding="utf-8")
        references = self._parser.parse(content)
        report.total_found = len(references)

        for ref in references:
            result = self._process_one(ref)
            report.results.append(result)

            if result.skipped:
                report.skipped += 1
            elif result.success:
                report.downloaded += 1
            else:
                report.failed += 1

        updated = self._rewriter.rewrite(
            content, report.results, self._asset_store, self._path
        )
        self._path.write_text(updated, encoding="utf-8")

        return report

    def _process_one(self, ref: ImageReference) -> DownloadResult:
        """Attempt to download a single ImageReference."""
        if self._downloader.is_data_uri(ref.url):
            return DownloadResult(reference=ref, skipped=True)

        if not self._downloader.is_remote(ref.url):
            return DownloadResult(reference=ref, skipped=True)

        destination = self._asset_store.allocate(ref.url)
        try:
            self._downloader.fetch(ref.url, destination)
            return DownloadResult(reference=ref, local_path=destination, success=True)
        except Exception as exc:  # noqa: BLE001
            destination.unlink(missing_ok=True)  # clean up empty/partial file
            return DownloadResult(reference=ref, success=False, error=str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python image_downloader.py <path-to-markdown-file>")
        sys.exit(1)

    markdown_path = Path(sys.argv[1]).resolve()

    if not markdown_path.exists():
        print(f"Error: file not found — {markdown_path}")
        sys.exit(1)

    if markdown_path.suffix.lower() != ".md":
        print(f"Warning: expected a .md file, got '{markdown_path.suffix}' — proceeding anyway.")

    processor = MarkdownImageProcessor(markdown_path)
    report = processor.run()
    report.print_summary()

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
