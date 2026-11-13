# sastrakara

An Agent Skill that documents a software project for people who do not read
code. It reads what the code really does, then writes it up in warm, plain
language for business readers, as Markdown and as a Word file they can edit.

*Sastrakara* joins two Indonesian words of Sanskrit origin: *sastra* (writing)
and *kara* (maker). A maker of writing.

## What it does

```
/sastrakara the checkout flow              asks: Markdown first, or straight to DOCX
/sastrakara the checkout flow --md         Markdown only, for review
/sastrakara the checkout flow --docx       Markdown and DOCX
/sastrakara docx docs/features/checkout.md convert an existing document
/sastrakara all                            propose a document set for the project
```

Options: `--lang=id|en`, `--out=<folder>`, `--audience=internal|external`.

Each document follows one skeleton: summary, who it is for, the big picture,
how it works, where the data comes from, what it means for the business,
limits, key terms, and a technical appendix for the engineers.

## How it differs from asking for "some docs"

- **Written for non-technical readers.** Short sentences, every term explained
  once, everyday comparisons, no code or file paths in the main body.
- **Nothing invented.** Every statement traces to a file that was read, listed
  in the appendix. What the code does not answer is marked "to be confirmed",
  not guessed.
- **Secrets stay out.** It does not open `.env` or key files, and it describes
  configuration by name and purpose, never by value.
- **A reader check before saving.** Four questions, from sentence to page:
  would the reader miss it, where did it come from, does the word describe or
  decorate, is the shape earned. The check may delete but never add facts.
- **Markdown is the source, DOCX is generated.** Change the template and every
  document can be regenerated. A DOCX that someone edited in Word is never
  overwritten without an explicit choice.
- **Follows the project.** Project rules, the existing docs folder and the
  language already in use outrank the skill's defaults.

## Install

Place the `skills/sastrakara` folder where your agent loads skills.

Claude Code, one project:
```bash
cp -R skills/sastrakara /path/to/project/.claude/skills/
```
Claude Code, every project:
```bash
cp -R skills/sastrakara ~/.claude/skills/
```
Other agents that support the Agent Skills format use their own skills folder;
copy the same directory.

With the community `skills` CLI
([vercel-labs/skills](https://github.com/vercel-labs/skills)):

```bash
npx skills add drnhsproject/sastrakara --list
npx skills add drnhsproject/sastrakara --skill sastrakara
npx skills add drnhsproject/sastrakara --skill sastrakara -g
```

The CLI is a third-party tool and collects anonymous usage data; set
`DISABLE_TELEMETRY=1` to opt out. Skills run with your agent's permissions, so
read `SKILL.md` before installing any skill, this one included.

## Requirements

No other skill is needed. Everything the skill uses is in its own folder.

- Markdown output: none.
- DOCX output: [pandoc](https://pandoc.org/installing.html), Python 3 (standard
  library only) and bash. On Windows, run it from Git Bash or WSL.

## Where documents go

`docs/` by default, one folder per topic, with an index table in
`docs/README.md`. Pass `--out=<folder>` or name the folder in your project's
agent instructions to change it. An existing `docs/README.md` is not rewritten;
the index is appended as a section.

## Your own Word template

With no template in the project, the standard one in
`skills/sastrakara/assets/reference.docx` is used (A4, page number in the
footer).

To use your organisation's look:

1. Copy `assets/reference.docx` to `<docs>/_template/reference.docx`, or start
   from your own Word file. The converter looks for `_template/reference.docx`
   in the document's folder and every folder above it, up to the root of the
   git repository.
2. In Word, change the styles: `Title`, `Subtitle`, `Author`, `Heading 1` to
   `Heading 3`, `Body Text`, `First Paragraph`, `Compact` (lists and table
   cells), `Table`, plus header, footer and page size.
3. Regenerate the documents that were never edited by hand:
   `bash skills/sastrakara/scripts/md-to-docx.sh <file.md> --force`.

Only styles, header, footer and page setup are taken from the template. Its
page content, including a designed cover page or a logo on the first page, is
not carried over. The cover is built from the document's front matter:

```yaml
title: "Checkout Flow"
subtitle: "How an order is placed and paid"
author: "Platform team"
date: "1 October 2026"
lang: en-US
organization: "Example Ltd"
prepared_for: "Operations"
version: "1.0"
status: "Draft"
reviewer: ""
```

Empty fields are left out. `cover: false` keeps a plain title block. Cover
labels are in Indonesian or English according to `lang`; other languages get
English labels.

When Word opens a generated file it may ask to update fields. Answer yes: that
fills in the page numbers of the table of contents.

## Layout

```
skills/sastrakara/
  SKILL.md       flow, accuracy guard, reader check
  references/    voice-id.md, voice-en.md: phrasing, fixed strings, check examples
  assets/        document-skeleton.id.md, document-skeleton.en.md, reference.docx
  scripts/       md-to-docx.sh, finish-docx.py
```

## What has and has not been tested

Tested, on macOS with pandoc 3.11 and Python 3.13:
- The converter: standard template, a project template found in a parent
  folder, Indonesian and English documents, refusal to overwrite (exit 2),
  `--force`, rejection of unsafe and remote image paths (exit 3), a document
  with no title (exit 1), `cover: false`, an embedded image, and the template
  search outside a git repository. Output XML parsed as well-formed in every
  case.
- One full run by a fresh agent that followed only the skill, on a real web
  project, read-only, in Indonesian: one feature document, Markdown and DOCX,
  four "to be confirmed" items, no em dash. The 22 unclear points it reported
  were used to tighten the instructions; that revised text has not been re-run.
- Installing from GitHub with `npx skills add drnhsproject/sastrakara --skill
  sastrakara -a claude-code`: `--list` finds the skill, 8 files are copied,
  identical to this repository, and the installed converter runs.

Not tested:
- The `/sastrakara` command and automatic triggering from the description.
- The reader check in its current wording: the full run above used an earlier
  draft of that step.
- English documents written by an agent (only the converter was run on them).
- The generated DOCX opened in Microsoft Word, Google Docs or LibreOffice. The
  layout was only seen through a macOS Quick Look preview, which does not show
  page breaks or table borders.
- Linux and Windows.
- Languages other than Indonesian and English.
- Other pandoc versions. The converter edits the XML pandoc writes, so a very
  different version may need adjustments.

## License

MIT. See `LICENSE`.
