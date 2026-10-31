# Built-in papers

This repository does **not** ship official CET past papers, answer PDFs, or listening audio. Those materials may be copyrighted and are intentionally excluded.

Put your own `cet-glass-paper/v1` paper folders here only if you have the right to redistribute them:

```
assets/papers/<paper-id>/
  paper.json
  listening.mp3   # optional
```

Most users should use **Import Paper** in the app instead. Imported papers are written to the local user-data directory and never uploaded to this repository:

- Development: `data/papers/`
- Windows exe: `%APPDATA%\CETGlassLab\papers\`

See [`docs/paper_template.json`](../../docs/paper_template.json) and [`docs/IMPORT_FORMAT.md`](../../docs/IMPORT_FORMAT.md) for the schema.
