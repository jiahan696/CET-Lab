# Local data

This directory is for runtime data that must not be committed.

- `user_data.json` — history, wrong answers, wordbook, active exam, settings
- `papers/` — imported papers and listening audio
- `ai_config.json` — optional AI provider credentials

The app creates these files automatically. They are ignored by `.gitignore`.

For AI setup, copy [`../docs/ai_config.example.json`](../docs/ai_config.example.json) to `ai_config.json` and fill in your own key, or use the in-app **AI Settings** dialog.
