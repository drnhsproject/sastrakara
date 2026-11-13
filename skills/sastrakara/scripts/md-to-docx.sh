#!/usr/bin/env bash
# md-to-docx.sh: convert a sastrakara Markdown source into an editable DOCX.
#
# Usage: bash md-to-docx.sh <file.md> [--force] [--template <file.docx>]
#
# The DOCX is written next to the source (same name, .docx).
#
# Style template, first match wins:
#   1. --template <file.docx>
#   2. _template/reference.docx in the document's folder or any folder above it,
#      up to the project root (the folder that holds .git); outside a git
#      repository, only the document's folder and its parent
#   3. the standard template shipped with this skill (assets/reference.docx)
#
# An existing DOCX is never overwritten without --force, because someone may have
# edited it in Word. Image links are checked (see below) so a document cannot pull
# local files (for example .env) or remote URLs into the DOCX.
#
# Exit codes: 1 usage or missing tool, 2 target exists, 3 unsafe image.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USAGE="Usage: bash $0 <file.md> [--force] [--template <file.docx>]"
SOURCE_MARKDOWN=""
FORCE_OVERWRITE=""
REFERENCE_DOCX=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --force) FORCE_OVERWRITE="yes" ;;
    --template)
      shift
      REFERENCE_DOCX="${1:-}"
      if [ -z "$REFERENCE_DOCX" ] || [ ! -f "$REFERENCE_DOCX" ]; then
        echo "✗ Template not found: '$REFERENCE_DOCX'" >&2
        exit 1
      fi
      ;;
    --*) echo "✗ Unknown option: $1" >&2; echo "  $USAGE" >&2; exit 1 ;;
    *)
      if [ -n "$SOURCE_MARKDOWN" ]; then
        echo "✗ Only one Markdown file at a time." >&2; echo "  $USAGE" >&2; exit 1
      fi
      SOURCE_MARKDOWN="$1"
      ;;
  esac
  shift
done

if [ -z "$SOURCE_MARKDOWN" ] || [ ! -f "$SOURCE_MARKDOWN" ]; then
  echo "✗ Markdown source not found: '$SOURCE_MARKDOWN'" >&2
  echo "  $USAGE" >&2
  exit 1
fi

for TOOL in pandoc python3; do
  if ! command -v "$TOOL" >/dev/null 2>&1; then
    echo "✗ $TOOL is not installed. See https://pandoc.org/installing.html or https://www.python.org/downloads/" >&2
    exit 1
  fi
done

SOURCE_DIRECTORY="$(cd -P "$(dirname "$SOURCE_MARKDOWN")" && pwd)"

if [ -z "$REFERENCE_DOCX" ]; then
  # Outside a git repository there is no project root to stop at, so only the
  # document's folder and its parent are searched.
  if git -C "$SOURCE_DIRECTORY" rev-parse --show-toplevel >/dev/null 2>&1; then
    SEARCH_LEVELS=64
  else
    SEARCH_LEVELS=2
  fi
  SEARCH_DIRECTORY="$SOURCE_DIRECTORY"
  while [ "$SEARCH_LEVELS" -gt 0 ]; do
    if [ -f "$SEARCH_DIRECTORY/_template/reference.docx" ]; then
      REFERENCE_DOCX="$SEARCH_DIRECTORY/_template/reference.docx"
      break
    fi
    if [ -e "$SEARCH_DIRECTORY/.git" ] || [ "$SEARCH_DIRECTORY" = "/" ]; then
      break
    fi
    SEARCH_DIRECTORY="$(dirname "$SEARCH_DIRECTORY")"
    SEARCH_LEVELS=$((SEARCH_LEVELS - 1))
  done
fi
if [ -z "$REFERENCE_DOCX" ]; then
  REFERENCE_DOCX="$(cd -P "$SCRIPT_DIRECTORY/../assets" && pwd)/reference.docx"
fi
if [ ! -f "$REFERENCE_DOCX" ]; then
  echo "✗ Template not found: $REFERENCE_DOCX" >&2
  exit 1
fi

TARGET_DOCX="${SOURCE_MARKDOWN%.md}.docx"

if [ -L "$TARGET_DOCX" ] || [ -d "$TARGET_DOCX" ]; then
  echo "✗ $TARGET_DOCX is a symlink or directory; refusing to write through it." >&2
  exit 2
fi

if [ -e "$TARGET_DOCX" ] && [ -z "$FORCE_OVERWRITE" ]; then
  echo "✗ $TARGET_DOCX already exists and may contain manual edits." >&2
  echo "  Re-run with --force to overwrite, or rename the Markdown source (e.g. -v2)." >&2
  exit 2
fi

# pandoc's --sandbox blocks all image embedding, so an explicit guard replaces it:
# every image target must be a relative png/jpg/jpeg inside the document's own folder
# (no URL, no absolute path, no "..", no symlink). Anything else aborts the conversion.
IMAGE_TARGETS="$(grep -oE '!\[[^]]*\]\([^)[:space:]]+' "$SOURCE_MARKDOWN" | sed -E 's/^!\[[^]]*\]\(//' || true)"
while IFS= read -r IMAGE_TARGET; do
  [ -z "$IMAGE_TARGET" ] && continue
  case "$IMAGE_TARGET" in
    /*|*..*|*://*|*:*|~*) echo "✗ Unsafe image path: $IMAGE_TARGET" >&2; exit 3 ;;
  esac
  case "$IMAGE_TARGET" in
    *.png|*.jpg|*.jpeg) ;;
    *) echo "✗ Image must be png/jpg: $IMAGE_TARGET" >&2; exit 3 ;;
  esac
  if [ -L "$SOURCE_DIRECTORY/$IMAGE_TARGET" ] || [ ! -f "$SOURCE_DIRECTORY/$IMAGE_TARGET" ]; then
    echo "✗ Image missing or a symlink: $IMAGE_TARGET" >&2; exit 3
  fi
done <<< "$IMAGE_TARGETS"

# Heading of the table of contents: the document's own toc-title wins, otherwise it
# follows the document language.
TOC_TITLE_ARGUMENTS=()
if ! grep -qE '^toc-title:' "$SOURCE_MARKDOWN"; then
  if grep -qiE '^lang:[[:space:]]*"?id' "$SOURCE_MARKDOWN"; then
    TOC_TITLE_ARGUMENTS=(--metadata "toc-title=Daftar Isi")
  else
    TOC_TITLE_ARGUMENTS=(--metadata "toc-title=Table of Contents")
  fi
fi

PANDOC_TEMP="$(mktemp "${TMPDIR:-/tmp}/sastrakara-XXXXXX.docx")"
trap 'rm -f "$PANDOC_TEMP"' EXIT

pandoc \
  --from markdown-raw_attribute-raw_html \
  --to docx \
  --reference-doc="$REFERENCE_DOCX" \
  --resource-path="$SOURCE_DIRECTORY" \
  --toc --toc-depth=2 \
  "${TOC_TITLE_ARGUMENTS[@]}" \
  --output "$PANDOC_TEMP" \
  -- "$SOURCE_MARKDOWN"

# Cover page and table of contents (see finish-docx.py).
python3 -I "$SCRIPT_DIRECTORY/finish-docx.py" "$PANDOC_TEMP" "$SOURCE_MARKDOWN" "$TARGET_DOCX"

echo "✓ $TARGET_DOCX"
echo "  template: $REFERENCE_DOCX"
