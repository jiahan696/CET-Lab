# Security Policy

## Supported versions

The latest `main` branch and the latest GitHub release are supported.

## Reporting a vulnerability

Please do **not** open a public issue for a vulnerability that could expose user data, API keys, or arbitrary code execution.

Use GitHub's private **Report a vulnerability** flow (Security → Advisories) or contact the maintainers privately. Include:

- affected version/commit;
- reproduction steps;
- impact;
- a suggested fix if you have one.

We will acknowledge reports as soon as possible and coordinate disclosure after a fix is available.

## Secrets and local data

- CET Glass Lab stores the AI key in local JSON only:
  - development: `data/ai_config.json`
  - exe: `%APPDATA%\CETGlassLab\ai_config.json`
- Do not paste a real key into an issue, pull request, screenshot, or log.
- If a key was committed accidentally, revoke/rotate it immediately and remove it from Git history; deleting it from the latest commit is not sufficient.
- The app has no telemetry. It contacts an AI endpoint only when the user explicitly uses translation, scoring, or PDF import.
