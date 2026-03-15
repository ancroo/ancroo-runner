"""Convert webpage HTML to EPUB ebook."""

import base64
import io
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from ebooklib import epub


def _sanitize_filename(title: str) -> str:
    """Create a safe filename from the page title."""
    name = re.sub(r"[^\w\s-]", "", title).strip()
    name = re.sub(r"[\s]+", "-", name).lower()
    return name[:80] or "webpage"


def _clean_html(html: str) -> str:
    """Extract body content and remove scripts, styles, and non-content elements."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(["script", "style", "footer", "iframe", "noscript"]):
        tag.decompose()

    # lxml always wraps fragments in <html><body> — extract body contents only
    body = soup.body
    if body:
        return body.decode_contents()
    return soup.decode_contents()


def run(input: dict) -> dict:
    html = input.get("html", "")
    title = input.get("title", "Webpage")
    url = input.get("url", "")

    if not html:
        return {"result": "", "error": "No HTML content provided"}

    # Clean HTML and extract body content
    body_html = _clean_html(html)

    # Create EPUB
    book = epub.EpubBook()

    book.set_identifier(url or f"ancroo-{datetime.now(timezone.utc).isoformat()}")
    book.set_title(title)
    book.set_language("en")
    book.add_author("Ancroo Runner")

    # Add metadata
    if url:
        book.add_metadata("DC", "source", url)

    # Add default CSS
    style = epub.EpubItem(
        uid="style",
        file_name="style/default.css",
        media_type="text/css",
        content=b"body { font-family: serif; line-height: 1.6; margin: 1em; } "
        b"h1 { margin-bottom: 0.5em; } "
        b"img { max-width: 100%; height: auto; }",
    )
    book.add_item(style)

    # Create chapter from HTML content
    chapter = epub.EpubHtml(
        title=title,
        file_name="content.xhtml",
        lang="en",
    )

    # Wrap in valid XHTML structure
    chapter_html = f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{title}</title></head>
<body>
<h1>{title}</h1>
{body_html}
</body>
</html>"""

    chapter.set_content(chapter_html)
    chapter.add_item(style)
    book.add_item(chapter)

    # Add navigation
    book.toc = [chapter]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

    # Write to bytes
    buf = io.BytesIO()
    epub.write_epub(buf, book)
    epub_bytes = buf.getvalue()

    filename = f"{_sanitize_filename(title)}.epub"

    return {
        "result": base64.b64encode(epub_bytes).decode("ascii"),
        "filename": filename,
        "mime_type": "application/epub+zip",
    }
