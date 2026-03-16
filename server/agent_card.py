"""Build the A2A AgentCard with Calibre skill definitions."""

from __future__ import annotations

from a2a.types import AgentCard, AgentSkill, AgentCapabilities

from config.settings import get_settings


SKILLS: list[AgentSkill] = [
    AgentSkill(
        id="convert",
        name="Convert Ebook",
        description="Convert an ebook between formats (EPUB, PDF, MOBI, AZW3, etc.)",
        tags=["convert", "ebook", "format"],
        examples=[
            "Convert this EPUB to PDF",
            "Transform my book to AZW3 for Kindle",
        ],
    ),
    AgentSkill(
        id="metadata_read",
        name="Read Metadata",
        description="Read metadata (title, author, tags, etc.) from an ebook file.",
        tags=["metadata", "read", "ebook"],
        examples=[
            "What metadata does this EPUB have?",
            "Show me the author and title of this book",
        ],
    ),
    AgentSkill(
        id="metadata_write",
        name="Write Metadata",
        description="Update metadata fields on an ebook file.",
        tags=["metadata", "write", "edit", "ebook"],
        examples=[
            "Set the author to Isaac Asimov",
            "Change the title to Foundation",
        ],
    ),
    AgentSkill(
        id="metadata_fetch",
        name="Fetch Metadata",
        description="Fetch metadata from online sources by title, author, or ISBN.",
        tags=["metadata", "fetch", "lookup", "isbn"],
        examples=[
            "Look up metadata for ISBN 978-0553293357",
            "Fetch book info for Foundation by Asimov",
        ],
    ),
    AgentSkill(
        id="polish",
        name="Polish Ebook",
        description="Polish/optimize an EPUB or AZW3 file (embed fonts, compress images, etc.).",
        tags=["polish", "optimize", "epub"],
        examples=[
            "Polish this EPUB and embed fonts",
            "Optimize my ebook file",
        ],
    ),
    AgentSkill(
        id="library_search",
        name="Search Library",
        description="Search the Calibre library by title, author, tags, or free-text query.",
        tags=["library", "search", "catalog"],
        examples=[
            "Find all books by Terry Pratchett",
            "Search for books tagged 'science-fiction'",
        ],
    ),
    AgentSkill(
        id="library_add",
        name="Add to Library",
        description="Add one or more ebook files to the Calibre library.",
        tags=["library", "add", "import"],
        examples=[
            "Add this EPUB to my library",
            "Import these books into Calibre",
        ],
    ),
    AgentSkill(
        id="library_export",
        name="Export from Library",
        description="Export books from the Calibre library by ID, optionally in specific formats.",
        tags=["library", "export", "download"],
        examples=[
            "Export book #42 as EPUB",
            "Download books 1-5 from the library",
        ],
    ),
]


def build_agent_card() -> AgentCard:
    settings = get_settings()
    return AgentCard(
        name="Calibre Agent",
        description=(
            "Paid AI agent for Calibre ebook operations — format conversion, "
            "metadata management, library search, and more. "
            "Accepts USDC payment via x402 protocol."
        ),
        url=settings.base_url + "/",
        version="0.1.0",
        defaultInputModes=["text", "file"],
        defaultOutputModes=["text", "file"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=SKILLS,
    )
