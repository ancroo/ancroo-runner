"""Convert HTML to Markdown using markdownify."""

from markdownify import markdownify


def run(input: dict) -> dict:
    html = input.get("html", "")
    if not html:
        return {"result": ""}
    md = markdownify(html, heading_style="ATX", strip=["img", "script", "style"])
    return {"result": md.strip()}
