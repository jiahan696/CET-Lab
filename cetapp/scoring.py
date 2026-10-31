"""Grading and exam session helpers."""
from __future__ import annotations

import time
from typing import Any

from .utils import fmt_score, now_iso, uid

EXAM_DURATIONS: dict[str, int] = {"CET-4": 125 * 60, "CET-6": 130 * 60}
SECTION_MAX = {"listening": 248.5, "reading": 248.5, "translation": 213.0}
SECTION_CN = {"listening": "听力", "reading": "阅读", "translation": "翻译"}
TOTAL_MAX = 710.0


def is_correct(question: dict[str, Any], answer: list[str] | None) -> bool:
    if not answer:
        return False
    return {str(a).upper() for a in answer} == {
        str(a).upper() for a in question.get("answers", [])
    }


def create_session(
    questions: list[dict[str, Any]],
    level: str,
    duration_sec: int | None = None,
) -> dict[str, Any]:
    duration = int(duration_sec or EXAM_DURATIONS.get(level, EXAM_DURATIONS["CET-4"]))
    now = time.time()
    return {
        "id": uid(),
        "level": level,
        "started_at": now_iso(),
        "started_ts": now,
        "duration_sec": duration,
        "deadline_ts": now + duration,
        "answers": {},
        "marked": [],
        "current": 0,
        "question_ids": [q["id"] for q in questions],
        "saved_at": now_iso(),
        "auto_saved": True,
    }


def remaining_seconds(session: dict[str, Any]) -> int:
    try:
        deadline = float(session.get("deadline_ts", 0))
    except (TypeError, ValueError):
        return 0
    return max(0, int(round(deadline - time.time())))


def session_elapsed(session: dict[str, Any]) -> int:
    try:
        started = float(session.get("started_ts", 0))
    except (TypeError, ValueError):
        return 0
    duration = int(session.get("duration_sec", 0) or 0)
    return max(0, min(duration, int(time.time() - started)))


def score_exam(
    questions: list[dict[str, Any]],
    answers: dict[str, list[str]],
) -> dict[str, Any]:
    counts = {"listening": 0, "reading": 0, "translation": 0}
    correct_counts = {"listening": 0, "reading": 0, "translation": 0}
    correct = 0
    details: list[dict[str, Any]] = []
    for q in questions:
        category = q["category"]
        counts[category] += 1
        answer = list(answers.get(q["id"], []) or [])
        ok = is_correct(q, answer)
        if ok:
            correct += 1
            correct_counts[category] += 1
        details.append(
            {
                "question_id": q["id"],
                "category": category,
                "answer": answer,
                "correct_answer": list(q["answers"]),
                "is_correct": ok,
            }
        )
    sections: dict[str, float] = {}
    for category, maximum in SECTION_MAX.items():
        total = counts[category]
        sections[category] = round(
            (correct_counts[category] / total * maximum) if total else 0.0, 1
        )
    total_score = round(sum(sections.values()), 1)
    total_count = len(questions)
    return {
        "score": total_score,
        "max_score": TOTAL_MAX,
        "sections": sections,
        "section_correct": correct_counts,
        "section_counts": counts,
        "correct": correct,
        "total": total_count,
        "unanswered": sum(1 for q in questions if not answers.get(q["id"])),
        "accuracy": round((correct / total_count * 100.0) if total_count else 0.0, 1),
        "details": details,
    }


def build_history_record(
    session: dict[str, Any],
    questions: list[dict[str, Any]],
    completed_by: str = "manual",
) -> dict[str, Any]:
    result = score_exam(questions, session.get("answers", {}))
    return {
        "id": uid(),
        "session_id": session.get("id"),
        "level": session.get("level", "CET-4"),
        "started_at": session.get("started_at", now_iso()),
        "completed_at": now_iso(),
        "duration_sec": session_elapsed(session),
        "completed_by": completed_by,
        "answers": session.get("answers", {}),
        "marked": session.get("marked", []),
        "question_ids": session.get("question_ids", [q["id"] for q in questions]),
        **result,
    }


def score_line(result: dict[str, Any]) -> str:
    sections = result.get("sections", {})
    return (
        f"总分 {fmt_score(result.get('score', 0))} · "
        f"听力 {fmt_score(sections.get('listening', 0))} · "
        f"阅读 {fmt_score(sections.get('reading', 0))} · "
        f"翻译 {fmt_score(sections.get('translation', 0))}"
    )
