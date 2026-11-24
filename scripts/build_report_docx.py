"""Build docs/report.docx (editable Word version of the report).

Run scripts/build_report.py first: this script converts the generated
docs/report.html with pandoc, using docs/report-reference.docx for the styles,
then sizes table columns to their content and sets an A4 page.
Needs pandoc on PATH, plus Pillow and lxml.
"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TOTAL = 11906 - 2 * 1134  # A4 width minus 2 cm margins, in twentieths of a point


def n(tag):
    return "{%s}%s" % (W, tag)


def prepare_html():
    html = (DOCS / "report.html").read_text(encoding="utf-8")
    html = re.sub(r'<div class="titleblock">.*?</div>\s*</div>', "", html, count=1, flags=re.S)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S)

    def size(match):
        tag = match.group(0)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        w, h = Image.open(DOCS / src).size
        wide = "wide" in tag
        max_w, max_h = (16.0, 14.0) if wide else (12.0, 9.5)
        return tag.replace("<img ", '<img width="%.1fcm" ' % min(max_w, max_h * w / h))

    return re.sub(r"<img [^>]*>", size, html)


def fix_layout(document_xml):
    tree = etree.parse(str(document_xml))
    root = tree.getroot()
    for tbl in root.iter(n("tbl")):
        rows = tbl.findall(n("tr"))
        grid = tbl.find(n("tblGrid"))
        ncol = len(grid)
        need = [0.0] * ncol
        for row in rows:
            for i, tc in enumerate(row.findall(n("tc"))[:ncol]):
                text = "".join(tc.itertext())
                longest = max([len(w) for w in text.split()] + [0])
                need[i] = max(need[i], min(len(text), 45), longest * 1.6 + 2, 4)
        widths = [int(TOTAL * x / sum(need)) for x in need]
        widths[-1] += TOTAL - sum(widths)
        for col, width in zip(grid, widths):
            col.set(n("w"), str(width))
        tbl_w = tbl.find(n("tblPr")).find(n("tblW"))
        tbl_w.set(n("type"), "dxa")
        tbl_w.set(n("w"), str(TOTAL))
        for row in rows:
            for i, tc in enumerate(row.findall(n("tc"))[:ncol]):
                pr = tc.find(n("tcPr"))
                if pr is None:
                    pr = etree.Element(n("tcPr"))
                    tc.insert(0, pr)
                for old in pr.findall(n("tcW")):
                    pr.remove(old)
                cell_w = etree.Element(n("tcW"))
                cell_w.set(n("w"), str(widths[i]))
                cell_w.set(n("type"), "dxa")
                pr.insert(0, cell_w)
    for sect in root.iter(n("sectPr")):
        for tag in ("pgSz", "pgMar"):
            for old in sect.findall(n(tag)):
                sect.remove(old)
        page = etree.SubElement(sect, n("pgSz"))
        page.set(n("w"), "11906")
        page.set(n("h"), "16838")
        margins = etree.SubElement(sect, n("pgMar"))
        for key, value in dict(top="1134", right="1134", bottom="1134", left="1134",
                               header="567", footer="567", gutter="0").items():
            margins.set(n(key), value)
    tree.write(str(document_xml), xml_declaration=True, encoding="UTF-8", standalone=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "report.html").write_text(prepare_html(), encoding="utf-8")
        raw = tmp / "raw.docx"
        subprocess.run([
            "pandoc", str(tmp / "report.html"), "-f", "html", "-t", "docx",
            "--reference-doc", str(DOCS / "report-reference.docx"), "--no-highlight",
            "--resource-path", str(DOCS),
            "--metadata", "title=Eurovision Explorer",
            "--metadata", "subtitle=Project B report · Information Technology · Kinga Kerekes · 25 November 2026",
            "-o", str(raw)], check=True)
        unpacked = tmp / "u"
        with zipfile.ZipFile(raw) as z:
            z.extractall(unpacked)
        fix_layout(unpacked / "word" / "document.xml")
        out = DOCS / "report.docx"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(unpacked.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(unpacked).as_posix())
    print("wrote", out)


if __name__ == "__main__":
    main()
