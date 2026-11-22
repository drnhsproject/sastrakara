# Changelog

## 0.1.4

- Three new scripts take the mechanical work off the model, so a small or cheap model
  gets it right every time: `scripts/settle-facts.py` (Step 0: output folder, language,
  template, commit), `scripts/lint-doc.py` (placeholders, em dashes, code and paths in the
  body, secret shapes, emoji headings, appendix opener, filler words, long sentences) and
  `scripts/update-index.py` (the index row). SKILL.md now calls them. Tested on a sample
  document; not yet measured with a small model.
- `finish-docx.py`: checks the three arguments (existing .docx, existing .md, output .docx)
  before opening them.
- SKILL.md description: trigger phrases are English only; the skill still writes in
  Indonesian or English. Trigger behaviour not re-measured.

## 0.1.3

- Converter: the image guard now reads pandoc's own parse of the document
  (`scripts/check-images.py`). Reference-style images such as `![x][r]` with
  `[r]: ../file.png` used to pass the old text pattern and could embed a file
  from outside the document folder. Symlinked folders on the way to an image
  are refused as well.
- SKILL.md: the style template section is shorter; the details stay in the
  Step 0 table and the README.

## 0.1.2

README only: the meaning of the name is now one line (*śāstrakāra*, the
document maker), and the test notes record the DOCX check in WPS Office. The
skill itself is unchanged from 0.1.1.

## 0.1.1

- README: the meaning of the name (Sanskrit *śāstrakāra*).
- SKILL.md: clearer rules found by two more test runs (products without
  screens, names the reader types, index status, uncommitted changes, where
  "to be confirmed" markers go, when a project tool may be run).

## 0.1.0

First public version. Business-facing documentation from a codebase, in
Indonesian or English: Markdown source, DOCX through pandoc with a standard
style template or the project's own, a cover and a table of contents built by
the converter, an accuracy guard, and a reader check with examples per language.
