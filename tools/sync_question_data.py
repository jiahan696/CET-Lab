"""Regenerate cetapp/question_data.py from assets/questions.json."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
raw = (ROOT / "assets" / "questions.json").read_text(encoding="utf-8")
assert "'''" not in raw
target = ROOT / "cetapp" / "question_data.py"
target.write_text(
    '"""Generated fallback copy of assets/questions.json for mobile/packaged builds.\n\n'
    'Run tools/sync_question_data.py after editing the JSON bank.\n"""\n'
    "QUESTIONS_JSON = r'''" + raw + "'''\n",
    encoding="utf-8",
)
print(f"wrote {target} ({target.stat().st_size} bytes)")
