"""Convert HTML to Markdown using markdownify."""

import re

from markdownify import markdownify


def _extract_body(html: str) -> str:
    """Extract <body> content if present, stripping <head> and doctype."""
    match = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    # No <body> tag — strip <head> section and doctype if present
    html = re.sub(r"<!DOCTYPE[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"</?html[^>]*>", "", html, flags=re.IGNORECASE)
    return html


def run(input: dict) -> dict:
    html = input.get("html", "")
    if not html:
        return {"result": ""}
    html = _extract_body(html)
    md = markdownify(html, heading_style="ATX", strip=["img", "script", "style"])
    # Clean up whitespace artifacts from HTML structure
    # Collapse 3+ consecutive newlines into 2 (one blank line)
    md = re.sub(r"\n{3,}", "\n\n", md)
    # Remove lines that are only whitespace
    md = re.sub(r"\n[ \t]+\n", "\n\n", md)
    # Remove leading whitespace on lines (from HTML indentation)
    md = re.sub(r"\n[ \t]+", "\n", md)
    return {"result": md.strip()}
