"""MCP server exposing Calibre operations via cli-anything-calibre CLI.

Community usage: claude mcp add calibre -- uv run python -m mcp_server
"""

from __future__ import annotations

import json
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calibre", instructions="Calibre ebook tools for conversion, metadata, and library management.")


def _run_cli(*args: str, library: str | None = None) -> dict:
    """Run cli-anything-calibre with --json flag and return parsed output."""
    cmd = ["cli-anything-calibre", "--json", *args]
    if library:
        cmd.extend(["--library", library])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"CLI error: {result.stderr.strip() or result.stdout.strip()}")
    return json.loads(result.stdout)


# ── Convert ──


@mcp.tool()
def convert_ebook(input_path: str, output_path: str) -> dict:
    """Convert an ebook between formats (EPUB, PDF, MOBI, AZW3, DOCX, etc.).

    Args:
        input_path: Path to the source ebook file.
        output_path: Path for the converted output (extension determines format).
    """
    return _run_cli("convert", "run", input_path, output_path)


@mcp.tool()
def polish_ebook(input_path: str, output_path: str) -> dict:
    """Polish/optimize an EPUB or AZW3 file (embed fonts, compress images, etc.).

    Args:
        input_path: Path to the source ebook file.
        output_path: Path for the polished output.
    """
    return _run_cli("convert", "polish", input_path, output_path)


@mcp.tool()
def list_formats() -> dict:
    """List all supported ebook conversion formats."""
    return _run_cli("convert", "formats")


# ── Metadata ──


@mcp.tool()
def get_metadata(path: str) -> dict:
    """Read metadata (title, author, tags, etc.) from an ebook file.

    Args:
        path: Path to the ebook file.
    """
    return _run_cli("metadata", "get", path)


@mcp.tool()
def set_metadata(
    path: str,
    title: str | None = None,
    authors: str | None = None,
    tags: str | None = None,
    series: str | None = None,
    series_index: str | None = None,
    publisher: str | None = None,
    isbn: str | None = None,
    cover: str | None = None,
    comments: str | None = None,
) -> dict:
    """Update metadata fields on an ebook file.

    Args:
        path: Path to the ebook file.
        title: New title for the book.
        authors: New author(s) for the book.
        tags: Comma-separated tags.
        series: Series name.
        series_index: Position in the series.
        publisher: Publisher name.
        isbn: ISBN identifier.
        cover: Path to a cover image file.
        comments: Book description/comments.
    """
    args = ["metadata", "set", path]
    for flag, value in [
        ("--title", title),
        ("--authors", authors),
        ("--tags", tags),
        ("--series", series),
        ("--series-index", series_index),
        ("--publisher", publisher),
        ("--isbn", isbn),
        ("--cover", cover),
        ("--comments", comments),
    ]:
        if value is not None:
            args.extend([flag, str(value)])
    return _run_cli(*args)


@mcp.tool()
def fetch_metadata(
    title: str | None = None,
    authors: str | None = None,
    isbn: str | None = None,
) -> dict:
    """Fetch metadata from online sources by title, author, or ISBN.

    Args:
        title: Book title to search for.
        authors: Author name to search for.
        isbn: ISBN to look up.
    """
    args = ["metadata", "fetch"]
    if title:
        args.extend(["--title", title])
    if authors:
        args.extend(["--authors", authors])
    if isbn:
        args.extend(["--isbn", isbn])
    return _run_cli(*args)


# ── Library ──


@mcp.tool()
def search_library(query: str, library: str) -> dict:
    """Search the Calibre library by title, author, tags, or free-text query.

    Args:
        query: Search query string.
        library: Path to the Calibre library directory.
    """
    return _run_cli("library", "search", query, library=library)


@mcp.tool()
def list_books(
    library: str,
    search: str | None = None,
    fields: str | None = None,
    sort_by: str | None = None,
    limit: int | None = None,
) -> dict:
    """List books in the Calibre library with optional filtering.

    Args:
        library: Path to the Calibre library directory.
        search: Filter expression for books.
        fields: Comma-separated list of fields to include.
        sort_by: Field to sort results by.
        limit: Maximum number of results to return.
    """
    args = ["library", "list"]
    if search:
        args.extend(["--search", search])
    if fields:
        args.extend(["--fields", fields])
    if sort_by:
        args.extend(["--sort-by", sort_by])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    return _run_cli(*args, library=library)


@mcp.tool()
def library_info(library: str) -> dict:
    """Get information about the Calibre library (book count, formats, etc.).

    Args:
        library: Path to the Calibre library directory.
    """
    return _run_cli("library", "info", library=library)


# ── Book ──


@mcp.tool()
def add_books(paths: list[str], library: str) -> dict:
    """Add one or more ebook files to the Calibre library.

    Args:
        paths: List of file paths to add.
        library: Path to the Calibre library directory.
    """
    return _run_cli("book", "add", *paths, library=library)


@mcp.tool()
def show_book(book_id: int, library: str) -> dict:
    """Show detailed information about a specific book in the library.

    Args:
        book_id: ID of the book in the Calibre library.
        library: Path to the Calibre library directory.
    """
    return _run_cli("book", "show", str(book_id), library=library)


@mcp.tool()
def export_books(
    ids: list[int],
    library: str,
    output_dir: str,
    formats: str | None = None,
) -> dict:
    """Export books from the Calibre library by ID.

    Args:
        ids: List of book IDs to export.
        library: Path to the Calibre library directory.
        output_dir: Directory to export books to.
        formats: Comma-separated list of formats to export (e.g. "epub,pdf").
    """
    str_ids = [str(i) for i in ids]
    args = ["book", "export", *str_ids, "-o", output_dir]
    if formats:
        args.extend(["--formats", formats])
    return _run_cli(*args, library=library)
