# Localization tooling

These scripts produced and maintain the Simplified Chinese localization of the
desktop GUI (`squalr/src`). They are one-off maintenance tools and are not part
of the shipped application, but they are kept so that a future upstream merge
can be re-localized without rebuilding the glossary from scratch.

## Files

| File | Purpose |
| --- | --- |
| `translations.json` | English source text to Chinese translation table (the glossary). |
| `extract_strings.py` | Scans `squalr/src` for candidate user facing string literals and writes `strings.json`. |
| `summarize.py` | Turns `strings.json` into frequency and per-file reports for review. |
| `apply_translations.py` | Replaces every string literal whose exact source text is a glossary key, and reports unused keys. |
| `display_position_report.py` | Lists remaining ascii literals that sit in display positions (labels, tooltips, tables) so missed text is easy to spot. |

## Typical workflow after merging upstream changes

```sh
python scripts/localization/extract_strings.py
python scripts/localization/summarize.py
python scripts/localization/display_position_report.py
```

Review the generated report files, add any new English strings to
`translations.json`, then apply them:

```sh
python scripts/localization/apply_translations.py
cargo build -p squalr --release
```

## Translation rules used

- Translate only text a user can see: window titles, menus, buttons, labels,
  tooltips, placeholders, tables, dialogs, and user facing status text.
- Never translate identifiers: window ids, action ids, egui id salts, data type
  ids, container type ids, project item type ids, or file paths.
- Keep format placeholders (`{}`, `{:X}`, named placeholders) intact.
- Keep engine log messages in english unless they surface in the user interface.
- When a localized label is parsed back from stored data, keep english aliases so
  previously authored data still parses (see `StructViewerContainerMode`).
