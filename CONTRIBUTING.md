# Contributing

Thanks for improving CET Glass Lab.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests -v
flet run main.py
```

## Before opening a pull request

- Run `python -m unittest discover -s tests -v`.
- Run `python -m compileall -q cetapp main.py tools`.
- Keep changes focused; include a short description and screenshots for UI changes.
- Update `README.md` or docs when behavior changes.

## Do not commit

- real API keys, `data/ai_config.json`, or `.env` files;
- user history, wrong answers, wordbook, imported papers, or `%APPDATA%\CETGlassLab`;
- official CET PDFs, answer PDFs, listening audio, or scanned pages unless you have explicit redistribution rights;
- `dist/`, `build/`, `*.spec`, screenshots from local testing.

Use the self-authored fixture in `tests/fixtures/demo_paper.json` for tests. For a new import-format example, use original content only.

## Code style

- Python 3.10+ syntax; keep modules small and typed where practical.
- Prefer standard-library `unittest` (the suite has no pytest dependency).
- UI text is Chinese; code identifiers and docstrings can be English.
- Avoid adding a backend or telemetry — the app is local-first by design.

## Reporting bugs

Use the bug report template and include:

- Windows version, Python version, app version;
- exact steps and expected/actual result;
- relevant error text with secrets and personal paths removed.

For security issues, follow [`SECURITY.md`](SECURITY.md).
