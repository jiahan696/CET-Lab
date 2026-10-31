"""Question bank loading and validation."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

CATEGORIES = ("listening", "reading", "translation")
CATEGORY_LABELS = {
    "listening": "听力",
    "reading": "阅读",
    "translation": "翻译",
}
LEVELS = ("CET-4", "CET-6")


def _candidate_paths() -> list[Path]:
    paths: list[Path] = []
    env_assets = os.getenv("FLET_ASSETS_DIR")
    if env_assets:
        paths.append(Path(env_assets) / "questions.json")
    module_root = Path(__file__).resolve().parent.parent
    paths.append(module_root / "assets" / "questions.json")
    if getattr(sys, "_MEIPASS", None):
        paths.append(Path(sys._MEIPASS) / "assets" / "questions.json")
    paths.append(Path.cwd() / "assets" / "questions.json")
    paths.append(Path.cwd() / "data" / "questions.json")
    return paths


def question_bank_path() -> Path:
    for path in _candidate_paths():
        if path.is_file():
            return path
    raise FileNotFoundError("找不到内置题库 assets/questions.json")


def load_question_bank() -> list[dict[str, Any]]:
    try:
        path = question_bank_path()
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except FileNotFoundError:
        # Mobile builds can run the Python package from a zip where only Python
        # modules are guaranteed to be readable. Keep a generated copy in-package.
        from .question_data import QUESTIONS_JSON

        payload = json.loads(QUESTIONS_JSON)
    questions = payload.get("questions", payload)
    if not isinstance(questions, list):
        raise ValueError("题库格式错误：questions 必须是数组")
    validate_questions(questions)
    return questions


def validate_questions(questions: list[dict[str, Any]]) -> None:
    if len(questions) != 45:
        raise ValueError(f"题库应包含 45 道题，当前为 {len(questions)} 道")
    seen: set[str] = set()
    for q in questions:
        qid = q.get("id")
        if not qid or qid in seen:
            raise ValueError(f"题目 id 缺失或重复：{qid!r}")
        seen.add(qid)
        if q.get("category") not in CATEGORIES:
            raise ValueError(f"{qid}: 未知题型 {q.get('category')!r}")
        if q.get("level") not in LEVELS:
            raise ValueError(f"{qid}: 未知级别 {q.get('level')!r}")
        if q.get("type") not in ("single", "multiple"):
            raise ValueError(f"{qid}: 未知答题类型 {q.get('type')!r}")
        options = q.get("options")
        if not isinstance(options, list) or len(options) < 4:
            raise ValueError(f"{qid}: 选项数量不足")
        answers = q.get("answers")
        if not isinstance(answers, list) or not answers:
            raise ValueError(f"{qid}: 缺少标准答案")
        valid_keys = {chr(65 + i) for i in range(len(options))}
        if not set(answers).issubset(valid_keys):
            raise ValueError(f"{qid}: 答案不在选项范围内")
        if q["type"] == "single" and len(answers) != 1:
            raise ValueError(f"{qid}: 单选题必须只有一个答案")
        if q["type"] == "multiple" and len(answers) < 2:
            raise ValueError(f"{qid}: 多选题至少需要两个答案")
        if not q.get("explanation"):
            raise ValueError(f"{qid}: 缺少解析")


def format_question_reference(q: dict[str, Any]) -> str:
    return f"{CATEGORY_LABELS.get(q['category'], q['category'])} · {q['level']}"


def section_name(category: str) -> str:
    return {
        "listening": "PART I  ·  LISTENING COMPREHENSION",
        "reading": "PART II  ·  READING COMPREHENSION",
        "translation": "PART III  ·  TRANSLATION",
    }.get(category, category.upper())


def section_cn(category: str) -> str:
    return {
        "listening": "听力理解",
        "reading": "阅读理解",
        "translation": "翻译辨析",
    }.get(category, category)
