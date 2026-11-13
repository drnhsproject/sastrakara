#!/usr/bin/env python3
"""finish-docx.py: add to a pandoc DOCX the two things pandoc leaves out.

Usage: finish-docx.py <pandoc.docx> <source.md> <output.docx>

  * Cover page. Title and subtitle stay as pandoc wrote them (so they follow the
    template's Title and Subtitle styles). The author and date lines are replaced by
    the organisation, the recipient and a small version table, then a page break.
    Set `cover: false` in the front matter to keep pandoc's plain title block.
  * Table of contents. pandoc writes an empty field that only Word can fill. This
    script writes the entries itself, each one a link to its heading, so the list is
    readable in any viewer. Word fills in the page numbers when the file is opened.

Everything else (fonts, colours, headings, tables, header, footer, paper size) comes
from the reference template pandoc was given. Standard library only.

Front-matter keys read here: title, subtitle, author, date, lang, organization,
prepared_for, version, status, reviewer, cover.
"""
import re
import sys
import zipfile
from html import escape

LABELS = {
    "id": {
        "version": "Versi",
        "date": "Tanggal",
        "status": "Status",
        "author": "Disusun oleh",
        "reviewer": "Diperiksa oleh",
        "prepared_for": "Untuk",
        "draft": "Draf",
    },
    "en": {
        "version": "Version",
        "date": "Date",
        "status": "Status",
        "author": "Prepared by",
        "reviewer": "Reviewed by",
        "prepared_for": "Prepared for",
        "draft": "Draft",
    },
}
ALIASES = {"organisation": "organization"}


def read_front_matter(path):
    with open(path, encoding="utf8") as handle:
        text = handle.read().replace("\r\n", "\n")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    meta = {}
    if match:
        for line in match.group(1).splitlines():
            pair = re.match(r'^([A-Za-z_-]+):\s*["\']?(.*?)["\']?\s*$', line)
            if pair:
                key = pair.group(1).lower().replace("-", "_")
                meta.setdefault(ALIASES.get(key, key), pair.group(2))
    return meta


def paragraph(text, style="", properties="", run_properties=""):
    style_tag = f'<w:pStyle w:val="{style}"/>' if style else ""
    return (
        f"<w:p><w:pPr>{style_tag}{properties}</w:pPr><w:r><w:rPr>{run_properties}</w:rPr>"
        f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
    )


PAGE_BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
TITLE_BLOCK = r'<w:p>\s*<w:pPr>\s*<w:pStyle w:val="(?:%s)"\s*/>.*?</w:p>'


def version_table(meta, labels):
    columns = [
        (labels["version"], meta.get("version") or "1.0"),
        (labels["date"], meta.get("date", "")),
        (labels["status"], meta.get("status") or labels["draft"]),
        (labels["author"], meta.get("author", "")),
        (labels["reviewer"], meta.get("reviewer", "")),
    ]
    columns = [(label, value) for label, value in columns if value]

    def row(values, header):
        properties = '<w:trPr><w:tblHeader w:val="on"/></w:trPr>' if header else ""
        bold = "<w:b/><w:bCs/>" if header else ""
        cells = "".join(
            "<w:tc><w:tcPr/>" + paragraph(value, "Compact", '<w:jc w:val="center"/>', bold) + "</w:tc>"
            for value in values
        )
        return f"<w:tr>{properties}{cells}</w:tr>"

    return (
        '<w:tbl><w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:type="pct" w:w="5000"/>'
        '<w:jc w:val="center"/><w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="0" '
        'w:lastColumn="0" w:noHBand="0" w:noVBand="0" w:val="0020"/></w:tblPr>'
        + row([label for label, _ in columns], True)
        + row([value for _, value in columns], False)
        + "</w:tbl>"
    )


def build_cover(document, meta, labels):
    """Replace pandoc's author and date lines with the cover block."""
    document = re.sub(TITLE_BLOCK % "Author|Date", "", document, flags=re.S)
    block = list(re.finditer(TITLE_BLOCK % "Title|Subtitle", document, re.S))
    if not block:
        sys.exit("✗ pandoc wrote no title paragraph; is `title` set in the front matter?")
    lines = []
    if meta.get("organization"):
        lines.append(paragraph(meta["organization"], "Author"))
    if meta.get("prepared_for"):
        lines.append(paragraph(f'{labels["prepared_for"]}: {meta["prepared_for"]}', "Author"))
    spacer = '<w:p><w:pPr><w:spacing w:before="1200" w:after="0"/></w:pPr></w:p>'
    cover = "".join(lines) + spacer + version_table(meta, labels) + PAGE_BREAK
    end = block[-1].end()
    return document[:end] + cover + document[end:]


def text_width(document):
    """Printable width in twentieths of a point, for the right-aligned page numbers."""
    size = re.search(r'<w:pgSz[^>]*\bw:w="(\d+)"', document)
    margins = re.search(r"<w:pgMar[^>]*>", document)
    if not size or not margins:
        return 9026
    left = re.search(r'w:left="(\d+)"', margins.group(0))
    right = re.search(r'w:right="(\d+)"', margins.group(0))
    if not left or not right:
        return 9026
    return int(size.group(1)) - int(left.group(1)) - int(right.group(1))


def build_table_of_contents(document):
    """Bookmark every Heading 1/2 and replace pandoc's empty TOC field with real entries."""
    if "<w:sdt>" not in document:
        return document
    entries = []

    def bookmark(match):
        level, block = match.group(1), match.group(0)
        text = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", block, re.S)).strip()
        name = f"_Toc9{len(entries):05d}"
        identifier = 90000 + len(entries)
        entries.append((int(level), text, name))
        start = f'<w:bookmarkStart w:id="{identifier}" w:name="{name}"/>'
        end = f'<w:bookmarkEnd w:id="{identifier}"/>'
        block = re.sub(r"(</w:pPr>)", r"\1" + start, block, count=1)
        return block.replace("</w:p>", end + "</w:p>")

    document = re.sub(
        r'<w:p>\s*<w:pPr>\s*<w:pStyle w:val="Heading([12])"\s*/>.*?</w:p>',
        bookmark,
        document,
        flags=re.S,
    )
    if not entries:
        return document

    tab = f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{text_width(document)}"/></w:tabs>'
    paragraphs = []
    for index, (level, text, name) in enumerate(entries):
        indent = '<w:ind w:left="240"/>' if level == 2 else ""
        run = "<w:rPr/>" if level == 2 else "<w:rPr><w:b/></w:rPr>"
        lead = (
            '<w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
            '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            if index == 0
            else ""
        )
        tail = '<w:r><w:fldChar w:fldCharType="end"/></w:r>' if index == len(entries) - 1 else ""
        page_number = (
            f'<w:r>{run}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{run}<w:instrText xml:space="preserve"> PAGEREF {name} \\h </w:instrText></w:r>'
            f'<w:r>{run}<w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r>{run}<w:fldChar w:fldCharType="end"/></w:r>'
        )
        paragraphs.append(
            f'<w:p><w:pPr>{tab}<w:spacing w:after="60"/>{indent}</w:pPr>{lead}'
            f'<w:hyperlink w:anchor="{name}" w:history="1">'
            f'<w:r>{run}<w:t xml:space="preserve">{text}</w:t></w:r><w:r>{run}<w:tab/></w:r>'
            f"{page_number}</w:hyperlink>{tail}</w:p>"
        )

    heading = re.search(r"<w:sdtContent>\s*(<w:p>.*?</w:p>)", document, re.S)
    sdt = (
        '<w:sdt><w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents"/>'
        "<w:docPartUnique/></w:docPartObj></w:sdtPr><w:sdtContent>"
        + (heading.group(1) if heading else "")
        + "".join(paragraphs)
        + "</w:sdtContent></w:sdt>"
        + PAGE_BREAK
    )
    return re.sub(r"<w:sdt>.*?</w:sdt>", lambda _: sdt, document, count=1, flags=re.S)


def main():
    if len(sys.argv) != 4:
        sys.exit("✗ Usage: finish-docx.py <pandoc.docx> <source.md> <output.docx>")
    pandoc_path, source_path, output_path = sys.argv[1:4]
    meta = read_front_matter(source_path)
    if not meta.get("title"):
        sys.exit("✗ front matter has no title")
    language = meta.get("lang", "en").lower()[:2]
    labels = LABELS.get(language, LABELS["en"])

    with zipfile.ZipFile(pandoc_path) as source:
        parts = {name: source.read(name) for name in source.namelist()}

    document = parts["word/document.xml"].decode("utf8")
    if meta.get("cover", "true").lower() not in ("false", "no", "off"):
        document = build_cover(document, meta, labels)
    document = build_table_of_contents(document)
    parts["word/document.xml"] = document.encode("utf8")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as target:
        for name, data in parts.items():
            target.writestr(name, data)


main()
