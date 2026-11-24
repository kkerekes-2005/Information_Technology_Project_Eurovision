"""Build docs/report.pdf from docs/report-source.md.

    python scripts/build_report.py

Markers in the source:
  {{include docs/queries.md rows=N}}  inserts the queries document without its title and
                                      first paragraph, keeping N result rows per query;
  {{schema}}                          inserts sql/schema.sql without comments and DROP lines.
The result is written as HTML and printed to PDF with Chromium (playwright).
Needs: pip install markdown playwright, then: playwright install chromium
"""
import asyncio
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def include(path, rows=None):
    text = (ROOT / path).read_text(encoding="utf-8")
    text = re.sub(r"\A# [^\n]*\n+[^\n#][^\n]*\n+", "", text)  # title and first paragraph
    if rows is None:
        return text
    out, kept = [], 0
    for line in text.split("\n"):
        if line.startswith("| "):
            kept += 1
            if kept > rows + 1:  # header row plus `rows` data rows
                continue
        elif not line.startswith("|"):
            kept = 0
        out.append(line)
    text = "\n".join(out)
    return re.sub(r"(Result: \d+ rows?\.) First \d+:", rf"\1 First {rows}:", text)


def schema():
    lines = (ROOT / "sql/schema.sql").read_text(encoding="utf-8").split("\n")
    kept = [line for line in lines
            if line.strip() and not line.lstrip().startswith("--")
            and not line.startswith("DROP TABLE")]
    return "\n".join(kept).replace(");\nCREATE", ");\n\nCREATE")


def expand(source):
    def do_include(match):
        parts = match.group(1).split()
        rows = int(parts[1].split("=")[1]) if len(parts) > 1 else None
        return include(parts[0], rows)
    source = re.sub(r"\{\{include ([^}]+)\}\}", do_include, source)
    return source.replace("{{schema}}", schema())


CSS = """
@page { size: A4; }
body { font-family: 'Inter', Arial, sans-serif; font-size: 9.5pt; line-height: 1.45; color: #222; }
.titleblock { margin-bottom: 14pt; padding-bottom: 8pt; border-bottom: 1.5pt solid #c21bbb; }
.t1 { font-family: 'Sora', Arial, sans-serif; font-size: 22pt; font-weight: 600; color: #6a1fb0; }
.t2 { font-size: 10pt; color: #555; margin-top: 2pt; }
h1 { font-family: 'Sora', Arial, sans-serif; font-size: 15pt; color: #6a1fb0; margin: 18pt 0 6pt;
     page-break-after: avoid; }
h2 { font-size: 11pt; margin: 12pt 0 4pt; color: #222; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 8.5pt; }
th { background: #f3eef6; text-align: left; padding: 3pt 5pt; border-bottom: 1pt solid #cbbfd3; }
td { border-bottom: 0.5pt solid #e2dbe6; padding: 3pt 5pt; vertical-align: top; }
tr { page-break-inside: avoid; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8pt; }
pre { background: #f7f5f8; border: 0.5pt solid #e2dbe6; padding: 6pt 8pt; font-size: 7.6pt;
      line-height: 1.3; white-space: pre-wrap; }
ul { margin: 4pt 0; padding-left: 16pt; }
li { margin-bottom: 2pt; }
figure { margin: 6pt 0 10pt; page-break-inside: avoid; }
figure img { max-width: 100%; }
figure img.wide { width: 100%; }
figcaption { font-size: 8pt; color: #555; margin-top: 2pt; }
.grid { display: flex; flex-wrap: wrap; gap: 10pt; }
.grid figure { width: calc(50% - 5pt); margin: 0; }
.grid figure img { max-height: 95mm; max-width: 100%; display: block; }
"""


def figures(html):
    """Turn each image into a figure whose caption is the image's alt text."""
    def to_figure(match):
        tag = match.group(0)
        alt = re.search(r'alt="([^"]*)"', tag).group(1)
        return f"<figure>{tag}<figcaption>{alt}</figcaption></figure>"
    html = re.sub(r"<p>(<img [^>]+>)</p>", r"\1", html)
    return re.sub(r"<img [^>]+>", to_figure, html)


async def to_pdf(html_path, pdf_path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(html_path.as_uri())
        await page.wait_for_timeout(1500)
        await page.pdf(path=str(pdf_path), format="A4", print_background=True,
                       display_header_footer=True, header_template="<span></span>",
                       footer_template='<div style="font-size:7pt;color:#888;width:100%;'
                                       'text-align:center">Kinga Kerekes · Eurovision Explorer'
                                       ' · <span class="pageNumber"></span></div>',
                       margin={"top": "16mm", "bottom": "16mm", "left": "16mm", "right": "16mm"})
        await browser.close()


def main():
    source = expand((DOCS / "report-source.md").read_text(encoding="utf-8"))
    body = markdown.markdown(source, extensions=["tables", "fenced_code", "attr_list", "md_in_html"])
    html = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f"<title>Eurovision Explorer: Project B report</title><style>{CSS}</style>"
            f"</head><body>{figures(body)}</body></html>")
    html_path = DOCS / "report.html"
    html_path.write_text(html, encoding="utf-8")
    asyncio.run(to_pdf(html_path, DOCS / "report.pdf"))
    print("docs/report.pdf written")


if __name__ == "__main__":
    main()
