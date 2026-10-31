"""Exam completion use-case shared by the live timer, manual submit and startup."""
from __future__ import annotations

from typing import Any

from .paperlib import paper_questions, score_paper
from .scoring import build_history_record, session_elapsed
from .store import Store
from .utils import now_iso, uid


def finalize_exam(
    store: Store,
    questions: list[dict[str, Any]],
    session: dict[str, Any],
    *,
    completed_by: str,
) -> dict[str, Any]:
    record = build_history_record(session, questions, completed_by=completed_by)
    wrong_items: list[tuple[str, list[str], str]] = []
    answers = session.get("answers", {}) or {}
    for detail in record["details"]:
        if detail["is_correct"]:
            continue
        user_answer = answers.get(detail["question_id"], []) or []
        if not user_answer:
            # Unanswered questions are reported, but not pushed into 错题本.
            continue
        wrong_items.append((detail["question_id"], list(user_answer), "exam"))
    store.complete_exam(record, wrong_items)
    return record


def finalize_paper_exam(
    store: Store,
    paper: dict[str, Any],
    session: dict[str, Any],
    *,
    writing_result: dict[str, Any] | None = None,
    translation_result: dict[str, Any] | None = None,
    completed_by: str = "manual",
) -> dict[str, Any]:
    answers = session.get("answers", {}) or {}
    result = score_paper(
        paper,
        answers,
        writing=writing_result,
        translation=translation_result,
    )
    meta = paper.get("paper", {})
    record = {
        "id": uid(),
        "session_id": session.get("id"),
        "paper_id": meta.get("id", ""),
        "paper_title": meta.get("title", ""),
        "level": meta.get("level", "CET-4"),
        "started_at": session.get("started_at", now_iso()),
        "completed_at": now_iso(),
        "duration_sec": session_elapsed(session),
        "completed_by": completed_by,
        "answers": answers,
        "text_answers": session.get("text_answers", {}) or {},
        "marked": session.get("marked", []),
        "question_ids": [q["id"] for q in paper_questions(paper)],
        **result,
    }
    wrong_items: list[tuple[str, list[str], str]] = []
    for detail in result["details"]:
        if detail["is_correct"]:
            continue
        if not detail["answer"]:
            continue
        wrong_items.append((detail["question_id"], detail["answer"], "exam"))
    store.complete_exam(record, wrong_items)
    return record
