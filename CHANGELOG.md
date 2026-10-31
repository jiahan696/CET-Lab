# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-11-01

### Added

- Liquid-glass Flet UI with responsive desktop/mobile navigation.
- Full mock exam flow: writing, listening audio, split-pane reading, translation.
- Absolute deadline countdown, autosave/resume, auto-submit, and history.
- AI selection translation with a persistent wordbook.
- AI writing/translation scoring (CET 15-point scale → 106.5).
- PDF + answer PDF + audio import with local parsing and optional AI vision OCR.
- Fixed `cet-glass-paper/v1` template and import documentation.
- 45 self-authored practice questions, wrongbook, wordbook, history charts.
- Windows DWM titlebar fix for visible caption buttons.
- Support for papers without a listening section.
- Unit tests for scoring, persistence, timer, paper schema, AI fallback, and wordbook.

### Changed

- Reading banks moved to the top of the right question pane.
- Section B hints show a complete first sentence (full paragraph on hover).
- Reading passages are reflowed into paragraphs with first-line indentation.
- Word bank uses readable cards instead of a single small text block.

### Security / distribution

- No API key is included in the repository.
- Official CET PDFs, answer PDFs, and listening audio are intentionally excluded.
- Runtime data, imported papers, build artifacts, and local screenshots are gitignored.
