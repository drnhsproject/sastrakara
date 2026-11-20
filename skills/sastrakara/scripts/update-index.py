#!/usr/bin/env python3
"""update-index.py: add or update a document's row in <docs>/README.md.

Usage: update-index.py <docs-folder> <document.md> --readers "<text>" --status draft|docx|manual

Takes title, date and language from the document's front matter and writes the row
in the language's column names and status words. Creates README.md when missing,
appends a marked section when README.md has no marker, never rewrites other text.
A row whose status is "edited by hand" is not changed back (exit 2).
Standard library only.
"""
import os
import re
import sys

MARK = "<!-- sastrakara-index -->"
TEXT = {
    "id": {
        "head": ["Dokumen", "Untuk siapa", "Tanggal", "Format", "Status"],
        "status": {"draft": "Draf MD", "docx": "DOCX", "manual": "DOCX diedit manual"},
        "title": "Indeks Dokumen",
    },
    "en": {
        "head": ["Document", "For whom", "Date", "Format", "Status"],
        "status": {"draft": "Draft MD", "docx": "DOCX", "manual": "DOCX edited by hand"},
        "title": "Document Index",
    },
}


def front(path):
    with open(path, encoding="utf8") as handle:
        text = handle.read().replace("\r\n", "\n")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    meta = {}
    for line in (match.group(1).splitlines() if match else []):
        pair = re.match(r'^([A-Za-z_-]+):\s*["\']?(.*?)["\']?\s*$', line)
        if pair:
            meta.setdefault(pair.group(1).lower(), pair.group(2))
    return meta


def cell(text):
    return text.replace("|", "/").replace("\n", " ").strip()


def main():
    args = sys.argv[1:]
    readers = status = ""
    positional = []
    while args:
        item = args.pop(0)
        if item == "--readers" and args:
            readers = args.pop(0)
        elif item == "--status" and args:
            status = args.pop(0)
        else:
            positional.append(item)
    if len(positional) != 2 or status not in ("draft", "docx", "manual") or not readers:
        sys.exit('✗ Usage: update-index.py <docs-folder> <document.md> --readers "<text>" --status draft|docx|manual')
    docs, document = positional
    if not os.path.isfile(document):
        sys.exit(f"✗ document not found: {document}")

    meta = front(document)
    if not meta.get("title"):
        sys.exit("✗ document has no title in its front matter")
    lang = "id" if meta.get("lang", "en").lower().startswith("id") else "en"
    words = TEXT[lang]
    link = os.path.relpath(os.path.realpath(document), os.path.realpath(docs)).replace(os.sep, "/")
    fmt = "MD" if status == "draft" else "MD, DOCX"
    row = "| " + " | ".join([f"[{cell(meta['title'])}]({link})", cell(readers),
                             cell(meta.get("date", "")), fmt, words["status"][status]]) + " |"

    readme = os.path.join(docs, "README.md")
    os.makedirs(docs, exist_ok=True)
    text = open(readme, encoding="utf8").read() if os.path.isfile(readme) else ""
    table = ["| " + " | ".join(words["head"]) + " |", "|---|---|---|---|---|"]

    if MARK not in text:
        block = f"{'' if not text else chr(10)}## {words['title']}\n\n{MARK}\n\n" + "\n".join(table + [row]) + "\n"
        text = (text.rstrip("\n") + "\n" if text else "") + block
        action = "added (new index section)"
    else:
        lines = text.split("\n")
        mark_at = lines.index(next(l for l in lines if MARK in l))
        end = mark_at + 1
        while end < len(lines) and (lines[end].strip() == "" or lines[end].lstrip().startswith("|")):
            end += 1
        hit = next((i for i in range(mark_at + 1, end) if f"]({link})" in lines[i]), None)
        if hit is not None:
            old = lines[hit]
            if words["status"]["manual"] in old and status != "manual":
                print(f"✗ {link} is marked '{words['status']['manual']}': the DOCX is the master. Not changed.", file=sys.stderr)
                sys.exit(2)
            lines[hit] = row
            action = "updated"
        else:
            tail = end
            while tail > mark_at + 1 and lines[tail - 1].strip() == "":
                tail -= 1
            if not any(l.lstrip().startswith("|") for l in lines[mark_at + 1:end]):
                lines[tail:tail] = [""] + table + [row]
            else:
                lines.insert(tail, row)
            action = "added"
        text = "\n".join(lines)
    with open(readme, "w", encoding="utf8") as handle:
        handle.write(text if text.endswith("\n") else text + "\n")
    print(f"✓ index row {action}: {readme}")


main()
