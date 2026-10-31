"""Paper library and scoring for imported CBT-style papers.

A paper is intentionally stored as one self-contained JSON document.  Audio
files live next to it so a paper folder is portable and can be moved/copied.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .utils import fmt_score, now_iso, uid

PAPER_SCHEMA = "cet-glass-paper/v1"
SECTION_MAX = {
    "writing": 106.5,
    "listening": 248.5,
    "reading": 248.5,
    "translation": 106.5,
}
SECTION_LABELS = {
    "writing": "写作",
    "listening": "听力",
    "reading": "阅读",
    "translation": "翻译",
}
TOTAL_MAX = 710.0


def assets_papers_dir() -> Path:
    env_assets = os.getenv("FLET_ASSETS_DIR")
    if env_assets:
        candidate = Path(env_assets) / "papers"
        if candidate.exists():
            return candidate
    module = Path(__file__).resolve().parent.parent / "assets" / "papers"
    if module.exists():
        return module
    if getattr(sys, "_MEIPASS", None):
        candidate = Path(sys._MEIPASS) / "assets" / "papers"
        if candidate.exists():
            return candidate
    return module


def data_papers_dir(data_dir: Path) -> Path:
    target = data_dir / "papers"
    target.mkdir(parents=True, exist_ok=True)
    return target


def normalize_question(
    raw: dict[str, Any],
    *,
    paper_id: str,
    paper_level: str,
    category: str,
    default_section: str = "",
    material: str = "",
) -> dict[str, Any]:
    qid = str(raw.get("id") or raw.get("number") or uid())
    options = raw.get("options") or []
    normalized_options: list[str] = []
    for option in options:
        if isinstance(option, dict):
            normalized_options.append(str(option.get("text", "")))
        else:
            normalized_options.append(str(option))
    answers = raw.get("answers") or raw.get("answer") or []
    if isinstance(answers, str):
        answers = [answers]
    return {
        **raw,
        "id": f"{paper_id}::{qid}",
        "raw_id": qid,
        "paper_id": paper_id,
        "category": category,
        "level": raw.get("level") or paper_level,
        "type": raw.get("type") or ("multiple" if len(answers) > 1 else "single"),
        "section": raw.get("section") or default_section,
        "material": raw.get("material") or material,
        "question": raw.get("question") or raw.get("stem") or "请选择最佳答案。",
        "options": normalized_options,
        "answers": [str(a).upper() for a in answers],
        "explanation": raw.get("explanation") or "导入试卷暂未生成解析。",
        "difficulty": raw.get("difficulty") or "进阶",
    }


def paper_questions(paper: dict[str, Any], *, include_subjective: bool = False) -> list[dict[str, Any]]:
    paper_meta = paper.get("paper", {})
    pid = paper_meta.get("id", "paper")
    level = paper_meta.get("level", "CET-4")
    rows: list[dict[str, Any]] = []
    for section in paper.get("listening", {}).get("sections", []):
        material = section.get("material", "")
        for q in section.get("questions", []):
            rows.append(
                normalize_question(
                    q,
                    paper_id=pid,
                    paper_level=level,
                    category="listening",
                    default_section=section.get("title", "Listening"),
                    material=material,
                )
            )
    for passage in paper.get("reading", {}).get("passages", []):
        material = passage.get("material", "")
        for q in passage.get("questions", []):
            rows.append(
                normalize_question(
                    q,
                    paper_id=pid,
                    paper_level=level,
                    category="reading",
                    default_section=passage.get("title", "Reading"),
                    material=material,
                )
            )
    if include_subjective:
        writing = paper.get("writing") or {}
        translation = paper.get("translation") or {}
        if writing:
            rows.append(
                {
                    "id": f"{pid}::writing",
                    "raw_id": "writing",
                    "paper_id": pid,
                    "category": "writing",
                    "level": level,
                    "type": "writing",
                    "section": writing.get("title", "Writing"),
                    "question": writing.get("prompt", ""),
                    "options": [],
                    "answers": [],
                    "explanation": writing.get("reference_answer", ""),
                    "max_score": writing.get("max_score", SECTION_MAX["writing"]),
                }
            )
        if translation:
            rows.append(
                {
                    "id": f"{pid}::translation",
                    "raw_id": "translation",
                    "paper_id": pid,
                    "category": "translation",
                    "level": level,
                    "type": "translation",
                    "section": translation.get("title", "Translation"),
                    "question": translation.get("prompt", ""),
                    "options": [],
                    "answers": [],
                    "explanation": translation.get("reference_answer", ""),
                    "max_score": translation.get("max_score", SECTION_MAX["translation"]),
                }
            )
    return rows


def paper_summary(paper: dict[str, Any]) -> dict[str, Any]:
    listening = sum(
        len(section.get("questions", []))
        for section in paper.get("listening", {}).get("sections", [])
    )
    reading = sum(
        len(passage.get("questions", []))
        for passage in paper.get("reading", {}).get("passages", [])
    )
    meta = paper.get("paper", {})
    return {
        "id": meta.get("id", ""),
        "title": meta.get("title", "未命名试卷"),
        "level": meta.get("level", "CET-4"),
        "duration_sec": int(meta.get("duration_sec", 125 * 60)),
        "source": meta.get("source", "imported"),
        "listening": listening,
        "reading": reading,
        "created_at": meta.get("created_at", ""),
        "has_audio": bool(paper.get("listening", {}).get("audio")),
    }


class PaperLibrary:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.imported_dir = data_papers_dir(self.data_dir)
        self.papers: list[dict[str, Any]] = []
        self.reload()

    def reload(self) -> None:
        papers: list[dict[str, Any]] = []
        # Built-in sample paper(s)
        builtin = assets_papers_dir()
        if builtin.exists():
            for path in sorted(builtin.glob("*/paper.json")):
                paper = self._load(path)
                if paper:
                    paper["_path"] = str(path)
                    paper["_builtin"] = True
                    papers.append(paper)
        # User-imported papers
        for path in sorted(self.imported_dir.glob("*/paper.json")):
            paper = self._load(path)
            if paper:
                paper["_path"] = str(path)
                paper["_builtin"] = False
                papers.append(paper)
        # Newest imported first, built-in sample first overall.
        builtin_papers = [p for p in papers if p.get("_builtin")]
        imported_papers = sorted(
            [p for p in papers if not p.get("_builtin")],
            key=lambda p: p.get("paper", {}).get("created_at", ""),
            reverse=True,
        )
        self.papers = builtin_papers + imported_papers

    def _load(self, path: Path) -> dict[str, Any] | None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw.get("schema") != PAPER_SCHEMA:
                return None
            return raw
        except (OSError, json.JSONDecodeError):
            return None

    def get(self, paper_id: str) -> dict[str, Any] | None:
        for paper in self.papers:
            if paper.get("paper", {}).get("id") == paper_id:
                return paper
        return None

    def get_by_question_id(self, qid: str) -> dict[str, Any] | None:
        for paper in self.papers:
            for q in paper_questions(paper):
                if q["id"] == qid:
                    return q
        return None

    def audio_path(self, paper: dict[str, Any]) -> Path | None:
        meta = paper.get("paper", {})
        base = Path(paper.get("_path", "")).parent if paper.get("_path") else None
        candidates: list[Path] = []
        rel = paper.get("listening", {}).get("audio") or meta.get("audio")
        if rel:
            if base:
                candidates.append(base / rel)
            candidates.append(self.data_dir / rel)
        if base:
            candidates.extend(
                [
                    base / "listening.mp3",
                    base / "listening.m4a",
                    base / "listening.wav",
                ]
            )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def save_imported(
        self,
        paper: dict[str, Any],
        *,
        audio_source: Path | None = None,
        cover_source: Path | None = None,
    ) -> dict[str, Any]:
        paper_id = paper.setdefault("paper", {}).setdefault("id", "paper-" + uid()[:8])
        target_dir = self.imported_dir / paper_id
        target_dir.mkdir(parents=True, exist_ok=True)
        if audio_source and Path(audio_source).exists():
            suffix = Path(audio_source).suffix or ".mp3"
            audio_name = "listening" + suffix
            shutil.copy2(audio_source, target_dir / audio_name)
            paper["paper"]["audio"] = audio_name
            paper.setdefault("listening", {})["audio"] = audio_name
        if cover_source and Path(cover_source).exists():
            shutil.copy2(cover_source, target_dir / ("cover" + Path(cover_source).suffix))
        paper["paper"]["created_at"] = paper.get("paper", {}).get("created_at") or now_iso()
        target = target_dir / "paper.json"
        target.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
        self.reload()
        return paper

    def delete_imported(self, paper_id: str) -> None:
        for paper in list(self.papers):
            if paper.get("paper", {}).get("id") == paper_id and not paper.get("_builtin"):
                path = Path(paper.get("_path", ""))
                if path.is_file():
                    shutil.rmtree(path.parent, ignore_errors=True)
        self.reload()

    def all_objective_questions(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for paper in self.papers:
            rows.extend(paper_questions(paper))
        return rows


def score_paper(
    paper: dict[str, Any],
    answers: dict[str, list[str]],
    *,
    writing: dict[str, Any] | None = None,
    translation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    questions = paper_questions(paper)
    counts = {"listening": 0, "reading": 0}
    correct_counts = {"listening": 0, "reading": 0}
    details: list[dict[str, Any]] = []
    correct = 0
    for q in questions:
        cat = q["category"]
        if cat not in counts:
            continue
        counts[cat] += 1
        answer = [str(a).upper() for a in (answers.get(q["id"], []) or [])]
        ok = bool(answer) and set(answer) == set(q["answers"])
        if ok:
            correct += 1
            correct_counts[cat] += 1
        details.append(
            {
                "question_id": q["id"],
                "category": cat,
                "answer": answer,
                "correct_answer": q["answers"],
                "is_correct": ok,
            }
        )
    sections: dict[str, float] = {}
    for cat in ("listening", "reading"):
        sections[cat] = round(
            (correct_counts[cat] / counts[cat] * SECTION_MAX[cat]) if counts[cat] else 0.0,
            1,
        )
    sections["writing"] = round(float((writing or {}).get("score_106", 0) or 0), 1)
    sections["translation"] = round(float((translation or {}).get("score_106", 0) or 0), 1)
    counts["writing"] = 1
    counts["translation"] = 1
    objective_total = counts["listening"] + counts["reading"]
    total_score = round(sum(sections.values()), 1)
    return {
        "score": total_score,
        "max_score": TOTAL_MAX,
        "sections": sections,
        "section_correct": correct_counts,
        "section_counts": counts,
        "correct": correct,
        "total": objective_total,
        "objective_total": objective_total,
        "unanswered": sum(1 for q in questions if not answers.get(q["id"])),
        "accuracy": round(
            (correct / objective_total * 100.0) if objective_total else 0.0, 1
        ),
        "details": details,
        "writing": writing or {},
        "translation": translation or {},
    }


def score_label(value: float) -> str:
    return fmt_score(value)
