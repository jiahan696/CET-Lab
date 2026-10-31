"""Local JSON persistence. No backend, no database, no network."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

from .utils import now_iso

DATA_FILENAME = "user_data.json"


def default_data_dir() -> Path:
    """Return a writable, per-user data directory for both dev and packaged app."""
    flet_dir = os.getenv("FLET_APP_STORAGE_DATA")
    if flet_dir:
        return Path(flet_dir)
    if getattr(sys, "frozen", False):
        base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / "CETGlassLab"
        return Path.home() / ".cet_glass_lab"
    return Path(__file__).resolve().parent.parent / "data"


def default_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "history": [],
        "wrongbook": {},
        "wordbook": {},
        "practice": {
            "attempts": 0,
            "correct": 0,
            "by_category": {
                "listening": {"attempts": 0, "correct": 0},
                "reading": {"attempts": 0, "correct": 0},
                "translation": {"attempts": 0, "correct": 0},
            },
        },
        "active_exam": None,
    }


class Store:
    """Tiny atomic JSON store. Safe enough for a single-user desktop app."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else default_data_dir() / DATA_FILENAME
        self._lock = threading.RLock()
        self.last_error: str | None = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            data = default_payload()
            self._atomic_write(data)
            return data
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("root must be an object")
        except (OSError, ValueError, json.JSONDecodeError):
            stamp = now_iso().replace(":", "-")
            try:
                shutil.copy2(self.path, self.path.with_name(f"user_data.corrupt-{stamp}.json"))
            except OSError:
                pass
            data = default_payload()
            self._atomic_write(data)
            return data
        return self._normalize(data)

    def _normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        base = default_payload()
        base.update(data)
        if not isinstance(base.get("history"), list):
            base["history"] = []
        if not isinstance(base.get("wrongbook"), dict):
            base["wrongbook"] = {}
        if not isinstance(base.get("wordbook"), dict):
            base["wordbook"] = {}
        practice = base.get("practice")
        if not isinstance(practice, dict):
            practice = default_payload()["practice"]
        for category in ("listening", "reading", "translation"):
            cat = practice.get("by_category", {}).get(category)
            if not isinstance(cat, dict):
                practice.setdefault("by_category", {})[category] = {
                    "attempts": 0,
                    "correct": 0,
                }
        practice.setdefault("attempts", 0)
        practice.setdefault("correct", 0)
        base["practice"] = practice
        if not isinstance(base.get("active_exam"), dict):
            base["active_exam"] = None
        return base

    def _atomic_write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        tmp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".user_data-",
                suffix=".tmp",
                delete=False,
            ) as fh:
                tmp_name = fh.name
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
            self.last_error = None
        except OSError as exc:
            self.last_error = str(exc)
            if tmp_name:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
            raise

    def save(self) -> bool:
        with self._lock:
            self.data["updated_at"] = now_iso()
            try:
                self._atomic_write(self.data)
                return True
            except OSError:
                return False

    # ---------------------------------------------------------- active exam
    @property
    def active_exam(self) -> dict[str, Any] | None:
        active = self.data.get("active_exam")
        return active if isinstance(active, dict) else None

    def set_active_exam(self, session: dict[str, Any] | None) -> bool:
        with self._lock:
            self.data["active_exam"] = session
        return self.save()

    def clear_active_exam(self) -> bool:
        return self.set_active_exam(None)

    # ------------------------------------------------------------- history
    def add_history(self, record: dict[str, Any]) -> bool:
        with self._lock:
            self.data.setdefault("history", []).append(record)
        return self.save()

    def history(self) -> list[dict[str, Any]]:
        rows = [r for r in self.data.get("history", []) if isinstance(r, dict)]
        return sorted(rows, key=lambda r: r.get("completed_at", ""), reverse=True)

    # ------------------------------------------------------------ practice
    def record_practice(self, category: str, correct: bool) -> bool:
        with self._lock:
            practice = self.data["practice"]
            practice["attempts"] = int(practice.get("attempts", 0)) + 1
            if correct:
                practice["correct"] = int(practice.get("correct", 0)) + 1
            cat = practice.setdefault("by_category", {}).setdefault(
                category, {"attempts": 0, "correct": 0}
            )
            cat["attempts"] = int(cat.get("attempts", 0)) + 1
            if correct:
                cat["correct"] = int(cat.get("correct", 0)) + 1
        return self.save()

    # ------------------------------------------------------------ wrongbook
    def add_wrong(
        self,
        question: dict[str, Any],
        answer: list[str],
        source: str,
    ) -> bool:
        with self._lock:
            self._wrong_entry(question["id"], answer, source)
        return self.save()

    def note_redo(self, qid: str) -> bool:
        with self._lock:
            item = self.data.setdefault("wrongbook", {}).get(qid)
            if isinstance(item, dict):
                item["redo_count"] = int(item.get("redo_count", 0)) + 1
        return self.save()

    def _wrong_entry(self, qid: str, answer: list[str], source: str) -> None:
        stamp = now_iso()
        book = self.data.setdefault("wrongbook", {})
        item = book.get(qid)
        if not isinstance(item, dict):
            item = {
                "question_id": qid,
                "wrong_count": 0,
                "first_wrong_at": stamp,
                "source": source,
            }
            book[qid] = item
        item["wrong_count"] = int(item.get("wrong_count", 0)) + 1
        item["last_wrong_at"] = stamp
        item["last_answer"] = list(answer)
        item["source"] = source
        item.setdefault("redo_count", 0)

    def complete_exam(
        self,
        record: dict[str, Any],
        wrong_items: list[tuple[str, list[str], str]],
    ) -> bool:
        """Persist history + wrong answers + clear the active exam in one write."""
        with self._lock:
            self.data.setdefault("history", []).append(record)
            for qid, answer, source in wrong_items:
                self._wrong_entry(qid, answer, source)
            self.data["active_exam"] = None
        return self.save()

    def remove_wrong(self, qid: str) -> bool:
        with self._lock:
            self.data.setdefault("wrongbook", {}).pop(qid, None)
        return self.save()

    def clear_wrong(self) -> bool:
        with self._lock:
            self.data["wrongbook"] = {}
        return self.save()

    # ------------------------------------------------------------- wordbook
    def add_word(
        self,
        term: str,
        translation: str,
        *,
        context: str = "",
        source: str = "",
        phonetic: str = "",
        part_of_speech: str = "",
        example: str = "",
    ) -> bool:
        term = (term or "").strip()
        if not term:
            return False
        key = term.lower()
        with self._lock:
            book = self.data.setdefault("wordbook", {})
            item = book.get(key)
            if not isinstance(item, dict):
                item = {
                    "id": key,
                    "term": term,
                    "added_at": now_iso(),
                    "lookup_count": 0,
                }
                book[key] = item
            item["translation"] = translation
            item["context"] = context[:800]
            item["source"] = source
            if phonetic:
                item["phonetic"] = phonetic
            if part_of_speech:
                item["part_of_speech"] = part_of_speech
            if example:
                item["example"] = example
            item["lookup_count"] = int(item.get("lookup_count", 0)) + 1
            item["updated_at"] = now_iso()
        return self.save()

    def words(self) -> list[dict[str, Any]]:
        items = [
            item
            for item in self.data.get("wordbook", {}).values()
            if isinstance(item, dict)
        ]
        return sorted(items, key=lambda i: i.get("added_at", ""), reverse=True)

    def remove_word(self, word_id: str) -> bool:
        with self._lock:
            self.data.setdefault("wordbook", {}).pop(word_id, None)
        return self.save()

    def clear_words(self) -> bool:
        with self._lock:
            self.data["wordbook"] = {}
        return self.save()

    def wrong_items(self) -> list[dict[str, Any]]:
        items = [
            item
            for item in self.data.get("wrongbook", {}).values()
            if isinstance(item, dict)
        ]
        return sorted(items, key=lambda i: i.get("last_wrong_at", ""), reverse=True)

    # --------------------------------------------------------------- stats
    def stats(self) -> dict[str, Any]:
        history = self.history()
        accuracies = [
            float(r.get("accuracy", 0)) for r in history if r.get("accuracy") is not None
        ]
        scores = [float(r.get("score", 0)) for r in history if r.get("score") is not None]
        practice = self.data.get("practice", {})
        attempts = int(practice.get("attempts", 0))
        correct = int(practice.get("correct", 0))
        return {
            "exam_count": len(history),
            "avg_accuracy": (sum(accuracies) / len(accuracies)) if accuracies else 0.0,
            "best_score": max(scores) if scores else 0.0,
            "last_score": scores[0] if scores else 0.0,
            "wrong_count": len(self.data.get("wrongbook", {})),
            "practice_attempts": attempts,
            "practice_accuracy": (correct / attempts * 100.0) if attempts else 0.0,
            "recent": history[:3],
        }

    def export_backup(self, destination: Path | str) -> Path:
        destination = Path(destination)
        self.save()
        shutil.copy2(self.path, destination)
        return destination
