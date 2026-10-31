# Publishing this project on GitHub

This repository is prepared to be published as source only. Do not upload exam PDFs, answer PDFs, listening audio, build outputs, or local user data.

## 1. Pre-flight

From the project root:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q cetapp main.py tools
git status --ignored
```

Check that:

- `data/ai_config.json` does not exist or contains no real key;
- `data/user_data.json` and `data/papers/` are absent;
- `样卷/`, `assets/papers/sample_cet4/`, `dist/`, `build/`, `*.spec`, and local screenshots are ignored;
- no file contains `sk-...` or a personal Windows path.

A quick secret scan:

```powershell
Get-ChildItem -Recurse -File -Include *.py,*.json,*.md,*.txt,*.toml,*.yml,*.yaml |
  Select-String -Pattern 'sk-[A-Za-z0-9]{16,}'
```

## 2. Initialize and push

```powershell
git init -b main
git add .
git commit -m "Initial commit: CET Glass Lab"
git remote add origin https://github.com/<your-name>/cet-glass-lab.git
git push -u origin main
```

If you prefer GitHub CLI:

```powershell
gh repo create cet-glass-lab --public --source=. --remote=origin --push
```

## 3. Repository settings

Recommended settings in GitHub:

- **About**: add description, website (optional), and topics:
  `cet`, `cet4`, `cet6`, `flet`, `python`, `glassmorphism`, `exam`.
- **Actions**: enable workflows. `CI` runs tests; `Build Windows artifact` can be run manually or on a `v*` tag.
- **Security**:
  - enable Dependabot alerts and security updates;
  - enable secret scanning and push protection (public repos);
  - enable private vulnerability reporting;
  - point it at `SECURITY.md`.
- **Branches**: protect `main`, require the CI check before merge.
- **Releases**:
  - create a tag such as `v1.0.0`;
  - let the build workflow produce `CET-Glass-Lab.exe` as an artifact;
  - attach the exe to the release manually or with a release workflow.
- **License**: GitHub should detect the MIT license from `LICENSE`.

## 4. Before each release

```powershell
python -m unittest discover -s tests -v
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

- Verify the app starts and opens a paper import.
- Do not attach official exam material.
- Update [`CHANGELOG.md`](../CHANGELOG.md).
- Add the exe/zip to the GitHub Release, not to the source tree.

## 5. What is intentionally not included

- Official CET past papers, answer keys, listening audio, and scans.
- A bundled full mock paper. Users import their own legally obtained material.
- Any API key, history, wrong answers, wordbook, or imported paper.
- Built binaries (`dist/`) and local build directories.

The built-in 45 practice questions and the `tests/fixtures/demo_paper.json` fixture are self-authored CET-style content.
