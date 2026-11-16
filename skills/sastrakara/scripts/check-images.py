#!/usr/bin/env python3
"""check-images.py: refuse a document whose images could pull in files they should not.

Usage: pandoc -t json <file.md> | check-images.py <document-folder>

Reads pandoc's own parse of the document, so every image syntax is covered
(inline, reference-style, implicit references, images inside links or metadata)
instead of only the forms a text pattern would recognise.

Every image target must be a relative png/jpg/jpeg path to a regular file inside
the document's folder: no URL, no absolute path, no "..", no symlink anywhere on
the way, also after percent-decoding.

Exit codes: 0 all images safe, 3 an unsafe or missing image. Standard library only.
"""
import json
import os
import sys
from urllib.parse import unquote


def image_targets(node):
    """Yield the target of every Image element anywhere in the pandoc JSON tree."""
    if isinstance(node, dict):
        if node.get("t") == "Image":
            yield node["c"][2][0]
        for value in node.values():
            yield from image_targets(value)
    elif isinstance(node, list):
        for value in node:
            yield from image_targets(value)


def problem(target, folder):
    """Return why the target is refused, or None if it is safe."""
    for form in {target, unquote(target)}:
        if not form or form.startswith(("/", "\\", "~")) or ":" in form:
            return "unsafe image path"
        if ".." in form:
            return "unsafe image path"
    path = unquote(target)
    if not path.lower().endswith((".png", ".jpg", ".jpeg")):
        return "image must be png/jpg"
    folder = os.path.realpath(folder)
    candidate = os.path.join(folder, path)
    walked = folder
    for part in os.path.normpath(path).split(os.sep):
        walked = os.path.join(walked, part)
        if os.path.islink(walked):
            return "image path goes through a symlink"
    if not os.path.isfile(candidate):
        return "image missing"
    if os.path.commonpath([folder, os.path.realpath(candidate)]) != folder:
        return "image outside the document folder"
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit("✗ Usage: pandoc -t json <file.md> | check-images.py <document-folder>")
    document = json.load(sys.stdin)
    for target in image_targets(document):
        reason = problem(target, sys.argv[1])
        if reason:
            print(f"✗ {reason[0].upper()}{reason[1:]}: {target}", file=sys.stderr)
            sys.exit(3)


main()
