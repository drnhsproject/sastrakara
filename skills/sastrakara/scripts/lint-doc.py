#!/usr/bin/env python3
"""lint-doc.py: the mechanical part of the reader check and the accuracy guard.

Usage: lint-doc.py <file.md> [--external]

Finds what a script can find for certain, so the model only judges the rest:
placeholders left in the front matter, em dashes and code or paths in the body,
secret shapes anywhere, emoji in headings, missing fixed sections and strings,
filler words, long sentences and paragraphs. The technical appendix is exempt
from the body rules. With --external the appendix and the commit field must be absent.

Exit codes: 0 no ERROR (WARN lines are for review), 1 at least one ERROR,
2 usage. Standard library only.
"""
import re
import sys

STRINGS = {
    "id": {
        "appendix": "Lampiran Teknis",
        "opener": "Bagian ini untuk tim teknis. Pembaca bisnis boleh melewatinya.",
        "limits": "Batasan dan Hal yang Perlu Diperhatikan",
        "terms": "Istilah Penting",
        "tbc": "(perlu konfirmasi tim teknis)",
        "filler": ["seperti kita ketahui", "pada akhirnya", "dalam rangka", "kesimpulannya",
                   "mari kita", "dokumen ini akan", "canggih", "inovatif", "revolusioner",
                   "tak tertandingi", "solusi terbaik", "sangat disukai"],
    },
    "en": {
        "appendix": "Technical Appendix",
        "opener": "This section is for the technical team. Business readers can skip it.",
        "limits": "Limits and Things to Watch",
        "terms": "Key Terms",
        "tbc": "(to be confirmed by the technical team)",
        "filler": ["as we all know", "at the end of the day", "for the purpose of",
                   "in conclusion", "let us walk", "let's dive", "this document will",
                   "powerful", "innovative", "seamless", "cutting-edge", "robust",
                   "leverage", "game-changing", "users love"],
    },
}
PLACEHOLDERS = ["Document Title", "Judul Dokumen", "Team or writer name", "Nama tim atau penulis",
                "One sentence that says", "Satu kalimat yang menjelaskan"]
SECRETS = [
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key header"),
    (r"\bAKIA[0-9A-Z]{16}\b", "cloud access key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{20,}", "GitHub token"),
    (r"\bsk-[A-Za-z0-9_-]{20,}", "API key (sk-)"),
    (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}", "JWT"),
    (r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*[\"']?[^\s\"'<>(]{6,}", "value assigned to a secret-like name"),
    (r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)(?!\.\d)", "IP address"),
]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆✅❌]")
ABBREVIATION = re.compile(r"\b(e\.g|i\.e|etc|mis|dll|dst|dsb|vs|no|hlm)\.", re.I)


def main():
    args = sys.argv[1:]
    external = "--external" in args
    files = [a for a in args if not a.startswith("--")]
    if len(files) != 1:
        sys.exit("Usage: lint-doc.py <file.md> [--external]")
    with open(files[0], encoding="utf8") as handle:
        raw = handle.read().replace("\r\n", "\n")
    lines = raw.split("\n")
    findings = []

    def add(level, number, message):
        findings.append((level, number, message))

    meta, body_start = {}, 0
    if lines and lines[0] == "---":
        for index in range(1, len(lines)):
            if lines[index] == "---":
                body_start = index + 1
                break
            pair = re.match(r'^([A-Za-z_-]+):\s*["\']?(.*?)["\']?\s*$', lines[index])
            if pair:
                meta.setdefault(pair.group(1).lower(), (pair.group(2), index + 1))
    if not body_start:
        add("ERROR", 1, "no front matter")
    for key in ("title", "date", "lang"):
        if not meta.get(key, ("",))[0]:
            add("ERROR", 1, f"front matter '{key}' is empty or missing")
    for key, (value, number) in meta.items():
        if re.search(r"<[^>]+>", value) or any(p.lower() in value.lower() for p in PLACEHOLDERS):
            add("ERROR", number, f"front matter '{key}' still holds placeholder text: {value[:40]}")
    lang = "id" if meta.get("lang", ("en",))[0].lower().startswith("id") else "en"
    text = STRINGS[lang]
    commit = meta.get("commit", ("",))[0]
    if external and commit:
        add("ERROR", meta["commit"][1], "external audience: remove the 'commit' field")

    # Split the body into regions: body for business readers, appendix, fences.
    appendix_at = None
    in_fence = False
    region = []
    for index in range(body_start, len(lines)):
        line = lines[index]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            region.append("fence")
            continue
        if in_fence:
            region.append("fence")
            continue
        heading = re.match(r"^#{1,6}\s+(.*?)\s*#*$", line)
        if heading and heading.group(1).strip().lower() == text["appendix"].lower():
            appendix_at = index
        region.append("appendix" if appendix_at is not None else "body")
    offset = body_start

    if appendix_at is None:
        if not external:
            add("ERROR", len(lines), f"no '{text['appendix']}' heading")
    elif external:
        add("ERROR", appendix_at + 1, "external audience: remove the technical appendix")
    else:
        following = next((l for l in lines[appendix_at + 1:] if l.strip()), "")
        if text["opener"].lower() not in following.lower():
            add("ERROR", appendix_at + 2, f"appendix must open with: {text['opener']}")

    headings = [re.match(r"^#{1,6}\s+(.*?)\s*#*$", l).group(1).strip().lower()
                for l in lines[body_start:] if re.match(r"^#{1,6}\s+", l)]
    for name in ("limits", "terms"):
        if text[name].lower() not in headings:
            add("WARN", 1, f"section '{text[name]}' not found")

    # Secrets: everywhere, appendix and fences included.
    for index, line in enumerate(lines):
        if index < body_start:
            continue
        for pattern, label in SECRETS:
            if re.search(pattern, line):
                add("ERROR", index + 1, f"possible secret ({label}): remove or describe generically")

    sentences_seen = 0
    paragraph, paragraph_start = [], 0
    tbc_count = 0
    limits_has_tbc = False
    current = ""

    def close_paragraph():
        nonlocal paragraph, sentences_seen
        if paragraph:
            joined = " ".join(paragraph)
            clean = re.sub(r"`[^`]*`", "x", joined)
            clean = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", clean)
            clean = ABBREVIATION.sub(lambda m: m.group(0)[:-1], clean)
            parts = [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"(*])", clean) if s.strip()]
            if len(parts) > 4:
                add("WARN", paragraph_start, f"paragraph has {len(parts)} sentences (aim for 4 or fewer)")
            for sentence in parts:
                words = len(re.findall(r"\S+", re.sub(r"[*_]", "", sentence)))
                if words > 28:
                    add("WARN", paragraph_start, f"sentence of {words} words (aim for 20 or fewer): {sentence[:50]}...")
        paragraph = []

    for position, line in enumerate(lines[body_start:]):
        number = position + 1 + offset
        kind = region[position]
        if kind == "fence":
            continue
        heading = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", line)
        if heading:
            close_paragraph()
            current = heading.group(2).strip().lower()
            if EMOJI.search(heading.group(2)):
                add("ERROR", number, "emoji in a heading")
            continue
        if kind != "body":
            continue
        if text["tbc"].lower() in line.lower():
            if current == text["limits"].lower():
                limits_has_tbc = True
            else:
                tbc_count += 1
        if "—" in line and not line.lstrip().startswith(">"):
            add("ERROR", number, "em dash in the body: use a period, comma, colon or parentheses")
        if re.search(r"(?<![\w/])[\w.-]+(?:/[\w.-]+)+\.\w{1,5}\b", re.sub(r"\]\([^)]*\)", "]", line)):
            add("WARN", number, "file path in the body (belongs in the technical appendix)")
        if "`" in line:
            add("WARN", number, "code in the body: keep only a name the reader types or sees")
        if len(re.findall(r"\*\*[^*]+\*\*", line)) > 1:
            add("WARN", number, "several bold spans in one line: bold is for the one caution")
        lowered = line.lower()
        for word in text["filler"]:
            if word in lowered:
                add("WARN", number, f"filler or praise: '{word}'")
        if line.strip() == "" or line.startswith("|") or re.match(r"^\s*([-*+]|\d+[.)])\s", line):
            close_paragraph()
            if re.match(r"^\s*([-*+]|\d+[.)])\s", line):
                paragraph, paragraph_start = [re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", line)], number
                close_paragraph()
        else:
            if not paragraph:
                paragraph_start = number
            paragraph.append(line.strip())
    close_paragraph()

    fence_lines = [i + offset + 1 for i, k in enumerate(region) if k == "fence"]
    in_body_fence = [n for n in fence_lines if appendix_at is None or n - 1 < appendix_at]
    if in_body_fence:
        add("ERROR", in_body_fence[0], "code block before the technical appendix")

    if tbc_count and not limits_has_tbc:
        add("WARN", 1, f"{tbc_count} 'to be confirmed' marker(s) in the body but none listed under '{text['limits']}'")

    order = {"ERROR": 0, "WARN": 1}
    findings.sort(key=lambda f: (order[f[0]], f[1]))
    errors = sum(1 for f in findings if f[0] == "ERROR")
    for level, number, message in findings:
        print(f"{level} line {number}: {message}")
    print(f"{'✗' if errors else '✓'} {errors} error(s), {len(findings) - errors} warning(s): {files[0]}")
    sys.exit(1 if errors else 0)


main()
