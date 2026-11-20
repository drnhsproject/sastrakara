#!/usr/bin/env python3
"""settle-facts.py: settle the project facts of Step 0 so a model does not have to.

Usage: settle-facts.py [--out <folder>] [--lang <code>]   (run inside the project)

Prints one `key: value` line per fact: docs, docs_candidates, lang, lang_source,
skeleton, template, commit, dirty. Read only. Standard library only.
"""
import os
import re
import subprocess
import sys

SKIP = {"node_modules", ".git", "dist", "build", "vendor", "__pycache__"}
SKILL = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))


def git(*args):
    try:
        done = subprocess.run(["git", *args], capture_output=True, text=True, timeout=20)
        return done.stdout.strip() if done.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def index_folders():
    found = []
    for folder, names, files in os.walk("."):
        names[:] = [n for n in names if n not in SKIP]
        if "README.md" in files:
            path = os.path.join(folder, "README.md")
            try:
                with open(path, encoding="utf8", errors="replace") as handle:
                    if "sastrakara-index" in handle.read():
                        found.append(os.path.normpath(folder))
            except OSError:
                pass
    return sorted(found)


def front_lang(path):
    try:
        with open(path, encoding="utf8", errors="replace") as handle:
            head = handle.read(2000)
    except OSError:
        return ""
    match = re.match(r"---\n(.*?)\n---\n", head.replace("\r\n", "\n"), re.S)
    pair = re.search(r"^lang:\s*[\"']?([A-Za-z]{2})", match.group(1), re.M) if match else None
    return pair.group(1).lower() if pair else ""


def main():
    args = sys.argv[1:]
    out = lang = ""
    while args:
        flag = args.pop(0)
        if flag == "--out" and args:
            out = args.pop(0)
        elif flag == "--lang" and args:
            lang = args.pop(0)[:2].lower()
        else:
            sys.exit("✗ Usage: settle-facts.py [--out <folder>] [--lang <code>]")

    candidates = index_folders()
    if out:
        docs = out
    elif len(candidates) == 1:
        docs = candidates[0]
    elif candidates:
        docs = "ASK"
    else:
        docs = "docs"
    print(f"docs: {docs}")
    print(f"docs_candidates: {', '.join(candidates) if candidates else '-'}")

    source = "flag" if lang else ""
    if not lang and docs != "ASK" and os.path.isdir(docs):
        counts = {}
        for folder, names, files in os.walk(docs):
            names[:] = [n for n in names if n not in SKIP and n != "_template"]
            for name in files:
                if name.endswith(".md") and name != "README.md":
                    code = front_lang(os.path.join(folder, name))
                    if code:
                        counts[code] = counts.get(code, 0) + 1
        if counts:
            lang, source = max(counts, key=counts.get), "existing documents"
    print(f"lang: {lang or 'UNKNOWN'}")
    print(f"lang_source: {source or 'use the language the user writes in'}")

    base = docs if docs != "ASK" else "docs"
    code = lang if lang in ("id", "en") else "en"
    project_skeleton = os.path.join(base, "_template", "document-skeleton.md")
    print("skeleton: " + (project_skeleton if os.path.isfile(project_skeleton)
          else os.path.join(SKILL, "assets", f"document-skeleton.{code}.md")))
    project_template = os.path.join(base, "_template", "reference.docx")
    print("template: " + (project_template if os.path.isfile(project_template)
          else os.path.join(SKILL, "assets", "reference.docx")))
    print("voice: " + os.path.join(SKILL, "references", f"voice-{code}.md"))
    print(f"commit: {git('rev-parse', '--short', 'HEAD') or '-'}")
    dirty = [line[3:] for line in git("status", "--porcelain").splitlines()]
    print(f"dirty: {', '.join(dirty[:20]) if dirty else '-'}")


main()
