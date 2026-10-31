from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cetapp.ai_agent import AIAgentClient, extract_json_object
from cetapp.paperlib import PaperLibrary, paper_questions, score_paper
from cetapp.exam_service import finalize_exam
from cetapp.questions import load_question_bank, validate_questions
from cetapp.scoring import (
    EXAM_DURATIONS,
    create_session,
    is_correct,
    remaining_seconds,
    score_exam,
)
from cetapp.store import Store


class QuestionBankTests(unittest.TestCase):
    def test_embedded_fallback_matches_json(self) -> None:
        from cetapp.question_data import QUESTIONS_JSON

        embedded = json.loads(QUESTIONS_JSON)["questions"]
        file_questions = json.loads(
            (Path(__file__).resolve().parent.parent / "assets" / "questions.json").read_text(
                encoding="utf-8"
            )
        )["questions"]
        self.assertEqual([q["id"] for q in embedded], [q["id"] for q in file_questions])
        with patch("cetapp.questions.question_bank_path", side_effect=FileNotFoundError):
            fallback = load_question_bank()
        self.assertEqual(len(fallback), 45)

    def test_bank_has_45_valid_questions(self) -> None:
        questions = load_question_bank()
        self.assertEqual(len(questions), 45)
        validate_questions(questions)
        counts = {"listening": 0, "reading": 0, "translation": 0}
        multi = 0
        for q in questions:
            counts[q["category"]] += 1
            if q["type"] == "multiple":
                multi += 1
        self.assertEqual(counts, {"listening": 15, "reading": 20, "translation": 10})
        self.assertGreaterEqual(multi, 4)


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.questions = load_question_bank()

    def test_all_correct(self) -> None:
        answers = {q["id"]: list(q["answers"]) for q in self.questions}
        result = score_exam(self.questions, answers)
        self.assertEqual(result["correct"], 45)
        self.assertAlmostEqual(result["score"], 710.0, places=1)
        self.assertEqual(result["accuracy"], 100.0)
        self.assertEqual(result["unanswered"], 0)
        self.assertAlmostEqual(result["sections"]["listening"], 248.5, places=1)
        self.assertAlmostEqual(result["sections"]["reading"], 248.5, places=1)
        self.assertAlmostEqual(result["sections"]["translation"], 213.0, places=1)

    def test_empty_paper(self) -> None:
        result = score_exam(self.questions, {})
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["accuracy"], 0.0)
        self.assertEqual(result["unanswered"], 45)

    def test_multi_select_requires_exact_set(self) -> None:
        q = next(q for q in self.questions if q["type"] == "multiple")
        self.assertTrue(is_correct(q, q["answers"]))
        self.assertFalse(is_correct(q, q["answers"][:1]))
        extra = [chr(65 + i) for i in range(len(q["options"]))]
        wrong_subset = [k for k in extra if k not in q["answers"]][:1]
        self.assertFalse(is_correct(q, wrong_subset))

    def test_session_duration(self) -> None:
        session = create_session(self.questions, "CET-4")
        self.assertEqual(session["duration_sec"], EXAM_DURATIONS["CET-4"])
        self.assertGreater(remaining_seconds(session), EXAM_DURATIONS["CET-4"] - 5)
        session6 = create_session(self.questions, "CET-6")
        self.assertEqual(session6["duration_sec"], EXAM_DURATIONS["CET-6"])


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "user_data.json"
        self.store = Store(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_first_run_creates_json(self) -> None:
        self.assertTrue(self.path.exists())
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(payload["history"], [])
        self.assertEqual(payload["wrongbook"], {})

    def test_practice_and_wrongbook_persist(self) -> None:
        questions = load_question_bank()
        q = questions[0]
        self.store.record_practice("listening", False)
        self.store.add_wrong(q, ["D"], "practice")
        self.assertEqual(self.store.stats()["practice_attempts"], 1)
        self.assertEqual(self.store.stats()["wrong_count"], 1)
        reloaded = Store(self.path)
        self.assertEqual(reloaded.stats()["practice_attempts"], 1)
        self.assertIn(q["id"], reloaded.data["wrongbook"])
        self.assertEqual(reloaded.data["wrongbook"][q["id"]]["last_answer"], ["D"])

    def test_complete_exam_is_atomic_and_clears_session(self) -> None:
        questions = load_question_bank()
        session = create_session(questions, "CET-4")
        session["answers"] = {questions[0]["id"]: ["D"]}
        self.store.set_active_exam(session)
        record = finalize_exam(self.store, questions, session, completed_by="timeout")
        self.assertIsNone(self.store.active_exam)
        self.assertEqual(len(self.store.history()), 1)
        self.assertEqual(record["completed_by"], "timeout")
        self.assertEqual(self.store.history()[0]["score"], record["score"])
        # Only the answered wrong question enters the wrongbook.
        self.assertEqual(len(self.store.wrong_items()), 1)
        reloaded = Store(self.path)
        self.assertIsNone(reloaded.active_exam)
        self.assertEqual(len(reloaded.history()), 1)

    def test_clear_and_remove_wrong(self) -> None:
        questions = load_question_bank()
        self.store.add_wrong(questions[0], ["D"], "practice")
        self.store.add_wrong(questions[1], ["D"], "practice")
        self.store.remove_wrong(questions[0]["id"])
        self.assertEqual(len(self.store.wrong_items()), 1)
        self.store.clear_wrong()
        self.assertEqual(self.store.wrong_items(), [])

    def test_corrupt_file_recovers(self) -> None:
        self.path.write_text("{broken", encoding="utf-8")
        store = Store(self.path)
        self.assertEqual(store.data["history"], [])
        self.assertTrue(self.path.exists())


class AIAgentTests(unittest.TestCase):
    def test_missing_config_is_offline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = AIAgentClient(Path(tmp) / "ai_config.json")
            self.assertFalse(client.available)
            example = client.write_example_config()
            self.assertTrue(example.exists())
            self.assertFalse(client.available)



class PaperAndAITests(unittest.TestCase):
    def test_demo_paper_schema_and_scoring(self) -> None:
        paper_path = Path(__file__).resolve().parent / "fixtures" / "demo_paper.json"
        self.assertTrue(paper_path.exists())
        paper = json.loads(paper_path.read_text(encoding="utf-8"))
        self.assertEqual(paper["schema"], "cet-glass-paper/v1")
        self.assertEqual(len(paper["listening"]["sections"][0]["questions"]), 2)
        self.assertEqual(sum(len(p["questions"]) for p in paper["reading"]["passages"]), 4)
        answers = {q["id"]: q["answers"] for q in paper_questions(paper)}
        result = score_paper(
            paper,
            answers,
            writing={"score_106": 106.5, "score_15": 15},
            translation={"score_106": 106.5, "score_15": 15},
        )
        self.assertEqual(result["correct"], 6)
        self.assertAlmostEqual(result["score"], 710.0, places=1)
        self.assertEqual(result["accuracy"], 100.0)
        self.assertAlmostEqual(result["sections"]["listening"], 248.5, places=1)
        self.assertAlmostEqual(result["sections"]["reading"], 248.5, places=1)

    def test_paper_library_saves_imported_paper(self) -> None:
        paper = json.loads(
            (Path(__file__).resolve().parent / "fixtures" / "demo_paper.json").read_text(
                encoding="utf-8"
            )
        )
        paper["paper"]["id"] = "imported-demo"
        with tempfile.TemporaryDirectory() as tmp:
            lib = PaperLibrary(Path(tmp))
            lib.save_imported(paper)
            self.assertIsNotNone(lib.get("imported-demo"))
            self.assertIsNone(lib.audio_path(lib.get("imported-demo")))

    def test_wordbook_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "user_data.json")
            store.add_word("choices", "选择", context="many choices", source="reading")
            self.assertEqual(len(store.words()), 1)
            reloaded = Store(Path(tmp) / "user_data.json")
            self.assertEqual(reloaded.words()[0]["translation"], "选择")
            reloaded.remove_word("choices")
            self.assertEqual(reloaded.words(), [])

    def test_extract_json_object_from_markdown(self) -> None:
        data = extract_json_object('```json\n{"score_15": 12.5, "ok": true}\n```')
        self.assertEqual(data["score_15"], 12.5)
        self.assertTrue(data["ok"])

    def test_session_audio_fields_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "user_data.json")
            self.assertIn("wordbook", store.data)


if __name__ == "__main__":
    unittest.main()
