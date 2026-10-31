"""PDF-to-template import pipeline for CET-style papers.

The parser handles standard CET layout locally.  AI is layered on top for:
  * scanning answer PDFs / messy PDFs,
  * generating explanations,
  * drafting reference writing/translation answers.

The output is one self-contained JSON document following
``cet-glass-paper/v1`` and can be edited by hand.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

from pypdf import PdfReader

from .ai_agent import AIAgentClient, AIAgentError
from .paperlib import PAPER_SCHEMA
from .utils import now_iso, uid

Progress = Callable[[str, float], Awaitable[None] | None]


# ------------------------------------------------------------------ PDF text
def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\uf0b7", " ")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\n?-----\s*PAGE\s+\d+\s*\(\d+ chars\)\s*-----", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return clean_text("\n".join(parts))


def extract_pdf_page_images(path: Path) -> list[bytes]:
    reader = PdfReader(str(path))
    out: list[bytes] = []
    for page in reader.pages:
        try:
            images = list(page.images)
        except Exception:
            images = []
        if images:
            try:
                from io import BytesIO

                buf = BytesIO()
                images[0].image.convert("RGB").save(buf, format="JPEG", quality=84)
                out.append(buf.getvalue())
            except Exception:
                out.append(b"")
        else:
            out.append(b"")
    return out


# ------------------------------------------------------------------ parsing
def split_parts(text: str) -> dict[str, str]:
    boundaries = [
        ("writing", r"Part\s+I\s+Writing"),
        ("listening", r"Part\s+II\s+Listening"),
        ("reading", r"Part\s+III\s+Reading"),
        ("translation", r"Part\s+IV\s+Translation"),
        ("keys", r"KEYS"),
    ]
    positions = []
    for key, pattern in boundaries:
        m = re.search(pattern, text, re.I)
        if m:
            positions.append((key, m.start()))
    out: dict[str, str] = {}
    for i, (key, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(text)
        out[key] = text[start:end]
    return out


def strip_directions(section: str) -> str:
    m = re.search(
        r"Directions:.*?(?:Answer Sheet [12]\.|centre\.|once\.|more than once\.|words?\.)",
        section,
        re.S | re.I,
    )
    if m:
        return section[m.end():]
    m = re.search(r"Directions:.*?(?:\n\s*\n)", section, re.S | re.I)
    if m:
        return section[m.end():]
    return section


def parse_answer_key(text: str) -> dict[int, str]:
    if "KEYS" not in text:
        return {}
    tail = text.split("KEYS", 1)[1]
    answer: dict[int, str] = {}
    number_buffer: list[int] = []
    for raw_line in tail.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        tokens = line.split()
        if tokens and all(re.fullmatch(r"\d{1,2}", t) for t in tokens):
            number_buffer = [int(t) for t in tokens]
            continue
        if number_buffer and tokens and all(re.fullmatch(r"[A-O]", t) for t in tokens):
            if len(tokens) == len(number_buffer):
                for n, a in zip(number_buffer, tokens):
                    answer[n] = a
            number_buffer = []
    return answer


def _option_blocks(block: str) -> dict[str, str]:
    marks = list(re.finditer(r"(?<![A-Za-z])([A-D])\)\s*", block))
    found: dict[str, str] = {}
    for i, m in enumerate(marks):
        key = m.group(1)
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(block)
        value = re.sub(r"\s+", " ", block[start:end]).strip()
        if key not in found and value:
            found[key] = value
    return found


def parse_questions(text: str, numbers: range, *, has_stem: bool = False) -> dict[int, dict]:
    matches = list(re.finditer(r"(?m)^\s*(\d{1,2})\.\s*", text))
    result: dict[int, dict] = {}
    for i, m in enumerate(matches):
        n = int(m.group(1))
        if n not in numbers:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.end():end]
        block = re.split(
            r"\n\s*(?:Part\s+[IVX]+|Section\s+[ABC]|Passage\s+(?:One|Two))\b", block
        )[0]
        opts = _option_blocks(block)
        stem = ""
        if has_stem:
            first = re.split(r"(?<![A-Za-z])[A-D]\)\s*", block, maxsplit=1)[0]
            stem = re.sub(r"\s+", " ", first).strip()
        if len(opts) >= 2:
            result[n] = {"stem": stem, "options": opts}
    return result


def _parse_word_bank(bank_text: str) -> dict[str, str]:
    bank: dict[str, str] = {}
    for line in bank_text.splitlines():
        for m in re.finditer(r"([A-O])\)\s*(.*?)(?=\s+[A-O]\)|$)", line.strip()):
            key = m.group(1)
            value = re.sub(r"\s+", " ", m.group(2)).strip()
            if key not in bank and value:
                bank[key] = value
    return bank


def parse_cet_text(
    text: str,
    *,
    title: str,
    level: str = "CET-4",
    duration_sec: int = 125 * 60,
    audio_name: str = "listening.mp3",
    answer_text: str = "",
    answers_override: dict[int, str] | None = None,
) -> dict[str, Any]:
    parts = split_parts(text)
    answers = parse_answer_key(parts.get("keys", ""))
    if not answers and answer_text:
        answers = parse_answer_key(answer_text)
    if not answers and answers_override:
        answers = {int(k): str(v).upper() for k, v in answers_override.items()}
    if not answers:
        raise ValueError("未能从 PDF 中识别答案。请确认试卷含答案页，或同时上传答案解析 PDF。")

    writing_section = parts.get("writing", "")
    writing_prompt = re.sub(r"^.*?Directions:\s*", "", writing_section, count=1, flags=re.S | re.I)
    writing_prompt = re.sub(r"\s+", " ", writing_prompt).strip()

    listening_section = parts.get("listening", "")
    listening_qs = parse_questions(listening_section, range(1, 26), has_stem=False)
    # Some official third-set papers intentionally omit listening and say so
    # in Part II.  Do not fail the whole import; keep a zero-question section.
    has_listening = bool(listening_qs)

    reading_section = parts.get("reading", "")
    sec_a_start = reading_section.find("Section A")
    sec_b_start = reading_section.find("Section B")
    sec_c_start = reading_section.find("Section C")
    if min(sec_a_start, sec_b_start, sec_c_start) < 0:
        raise ValueError("未能识别阅读三个 Section 的边界。")
    sec_a = reading_section[sec_a_start:sec_b_start]
    sec_b = reading_section[sec_b_start:sec_c_start]
    sec_c = reading_section[sec_c_start:]

    # Section A: banked cloze
    first_blank = re.search(r"_{2,}\s*26\s*_{2,}", sec_a)
    bank_m = re.search(r"\n\s*A\)\s*", sec_a[first_blank.start():] if first_blank else sec_a)
    if first_blank and bank_m:
        breaks = list(re.finditer(r"\n[ \t]*\n", sec_a[: first_blank.start()]))
        passage_start = breaks[-1].end() if breaks else 0
        bank_start = first_blank.start() + bank_m.start()
        sec_a_passage = sec_a[passage_start:bank_start].strip()
        bank_text = sec_a[bank_start:]
    else:
        sec_a_passage = strip_directions(sec_a).strip()
        bank_text = ""
    bank = _parse_word_bank(bank_text)
    if not bank:
        raise ValueError("未能识别阅读 Section A 的选词填空词库。")
    sec_a_questions = []
    for n in range(26, 36):
        m = re.search(rf"([^.\n]*?_{2,}\s*{n}\s*_{2,}[^.\n]*\.?)", sec_a_passage)
        stem = re.sub(r"\s+", " ", m.group(1)).strip() if m else f"请为第 {n} 空选择最合适的单词。"
        sec_a_questions.append({"number": n, "stem": stem, "answer": answers.get(n, "")})

    # Section B: paragraph matching
    sec_b_after = strip_directions(sec_b)
    first_stmt = re.search(r"(?m)^\s*36\.\s*", sec_b_after)
    sec_b_passage = sec_b_after[: first_stmt.start()].strip() if first_stmt else sec_b_after.strip()
    sec_b_questions = parse_questions(sec_b_after, range(36, 46), has_stem=True)
    paragraphs: dict[str, str] = {}
    for m in re.finditer(
        r"(?m)^\s*([A-O])\)\s*(.+?)(?=\n\s*[A-O]\)\s|\n\s*\d{1,2}\.\s|$)",
        sec_b_passage,
        re.S,
    ):
        paragraphs[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
    if not paragraphs:
        for line in sec_b_passage.splitlines():
            m = re.match(r"\s*([A-O])\)\s*(.+)", line)
            if m:
                paragraphs[m.group(1)] = m.group(2).strip()

    # Section C
    sec_c_passages = []
    for name, start_pat, q_range in (
        ("Passage One", r"Passage\s+One", range(46, 51)),
        ("Passage Two", r"Passage\s+Two", range(51, 56)),
    ):
        m = re.search(start_pat, sec_c, re.I)
        if not m:
            continue
        sub = sec_c[m.end():]
        if name == "Passage One":
            sub = sub.split("Passage Two")[0]
        first_q = re.search(rf"(?m)^\s*{q_range.start}\.\s*", sub)
        material = sub[: first_q.start()].strip() if first_q else sub.strip()
        material = re.sub(r"^Questions\s+\d+\s+to\s+\d+.*?\n", "", material, flags=re.I)
        qs = parse_questions(sub, q_range, has_stem=True)
        sec_c_passages.append(
            {"name": name, "material": material, "questions": qs, "range": q_range}
        )

    translation_section = parts.get("translation", "")
    trans = strip_directions(translation_section).strip()

    paper_id = "paper-" + uid()[:10]
    paper = {
        "schema": PAPER_SCHEMA,
        "paper": {
            "id": paper_id,
            "title": title,
            "level": level,
            "duration_sec": duration_sec,
            "source": "imported",
            "audio": audio_name,
            "created_at": now_iso(),
            "has_listening": has_listening,
        },
        "writing": {
            "id": "writing",
            "title": "Part I Writing",
            "directions": writing_prompt,
            "prompt": writing_prompt,
            "word_limit": [120, 180] if level == "CET-4" else [150, 200],
            "reference_answer": "",
            "max_score": 106.5,
        },
        "listening": {
            "id": "listening",
            "title": "Part II Listening Comprehension",
            "audio": audio_name,
            "available": has_listening,
            "note": (
                "本卷未提供听力部分。"
                if not has_listening
                else ""
            ),
            "sections": [
                {
                    "id": "listening",
                    "title": "Listening Comprehension",
                    "questions": [
                        {
                            "id": f"L{n}",
                            "number": n,
                            "type": "single",
                            "question": "请根据录音内容选择最佳答案。",
                            "options": [
                                v for k, v in sorted(listening_qs.get(n, {}).get("options", {}).items())
                            ],
                            "answers": [answers.get(n, "")],
                            "explanation": "",
                        }
                        for n in sorted(listening_qs)
                    ],
                }
            ],
        },
        "reading": {
            "id": "reading",
            "title": "Part III Reading Comprehension",
            "passages": [
                {
                    "id": "reading-a",
                    "title": "Section A",
                    "display": "word_bank",
                    "directions": "选词填空：从 A-O 选项中为每个空选择最合适的单词。",
                    "material": sec_a_passage,
                    "bank": [{"key": k, "text": v} for k, v in sorted(bank.items())],
                    "questions": [
                        {
                            "id": f"R{q['number']}",
                            "number": q["number"],
                            "type": "single",
                            "question": q["stem"],
                            "options": [{"key": k, "text": v} for k, v in sorted(bank.items())],
                            "answers": [q["answer"]] if q["answer"] else [],
                            "explanation": "",
                        }
                        for q in sec_a_questions
                    ],
                },
                {
                    "id": "reading-b",
                    "title": "Section B",
                    "display": "paragraph_matching",
                    "directions": "段落匹配：为每句话选择对应的段落字母。",
                    "material": sec_b_passage,
                    "bank": [{"key": k, "text": paragraphs.get(k, "")[:80]} for k in paragraphs],
                    "questions": [
                        {
                            "id": f"R{n}",
                            "number": n,
                            "type": "single",
                            "question": sec_b_questions.get(n, {}).get("stem", f"第 {n} 题"),
                            "options": [{"key": k, "text": k} for k in "ABCDEFGHIJKLMNO"],
                            "answers": [answers.get(n, "")],
                            "explanation": "",
                        }
                        for n in range(36, 46)
                    ],
                },
                *[
                    {
                        "id": f"reading-c-{idx}",
                        "title": p["name"],
                        "display": "passage",
                        "directions": "仔细阅读：阅读左侧原文，回答右侧问题。",
                        "material": p["material"],
                        "questions": [
                            {
                                "id": f"R{n}",
                                "number": n,
                                "type": "single",
                                "question": p["questions"].get(n, {}).get("stem", f"第 {n} 题"),
                                "options": [
                                    v
                                    for k, v in sorted(
                                        p["questions"].get(n, {}).get("options", {}).items()
                                    )
                                ],
                                "answers": [answers.get(n, "")],
                                "explanation": "",
                            }
                            for n in p["range"]
                        ],
                    }
                    for idx, p in enumerate(sec_c_passages, 1)
                ],
            ],
        },
        "translation": {
            "id": "translation",
            "title": "Part IV Translation",
            "directions": "将下面的中文段落翻译成英文。",
            "prompt": trans,
            "reference_answer": "",
            "max_score": 106.5,
        },
    }
    return paper


# ------------------------------------------------------------------ AI enrichment
async def _progress(cb: Progress | None, message: str, value: float) -> None:
    if not cb:
        return
    result = cb(message, value)
    if hasattr(result, "__await__"):
        await result  # type: ignore[misc]


def _objective_items(paper: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for q in paper.get("listening", {}).get("sections", [{}])[0].get("questions", []):
        rows.append(
            {
                "id": q["id"],
                "number": q["number"],
                "category": "listening",
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "answer": q.get("answers", [""])[0],
            }
        )
    for passage in paper.get("reading", {}).get("passages", []):
        for q in passage.get("questions", []):
            rows.append(
                {
                    "id": q["id"],
                    "number": q["number"],
                    "category": "reading",
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "answer": q.get("answers", [""])[0],
                    "material": passage.get("material", "")[:900],
                }
            )
    return rows


async def enrich_with_ai(
    agent: AIAgentClient,
    paper: dict[str, Any],
    *,
    answer_context: str = "",
    progress: Progress | None = None,
) -> None:
    if not agent.available:
        return
    items = _objective_items(paper)
    if not items:
        return
    batch_size = 12
    total_batches = max(1, (len(items) + batch_size - 1) // batch_size)
    for bi in range(total_batches):
        batch = items[bi * batch_size : (bi + 1) * batch_size]
        await _progress(
            progress,
            f"AI 生成解析 {bi + 1}/{total_batches}…",
            0.55 + 0.30 * (bi / total_batches),
        )
        prompt = (
            "你是大学英语四六级阅卷老师。根据题目、选项和正确答案，生成简洁准确的中文解析。"
            "听力题没有逐字原文时，只根据选项语义和正确项做合理讲解，不要冒充原文。"
            "每题解析 45-100 字，只返回严格 JSON："
            "{\"explanations\":{\"L1\":\"...\",\"R26\":\"...\"}}。\n\n"
            f"题目：{json.dumps(batch, ensure_ascii=False)}\n"
            f"答案页参考（可能为空）：{answer_context[:7000]}\n"
        )
        try:
            data = await agent.chat_json(
                [
                    {"role": "system", "content": "只输出合法 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=8000,
            )
            exps = data.get("explanations") or {}
            for q in paper.get("listening", {}).get("sections", [{}])[0].get("questions", []):
                if q["id"] in exps:
                    q["explanation"] = str(exps[q["id"]])
            for passage in paper.get("reading", {}).get("passages", []):
                for q in passage.get("questions", []):
                    if q["id"] in exps:
                        q["explanation"] = str(exps[q["id"]])
        except Exception:
            continue
    await _progress(progress, "AI 生成写作与翻译参考…", 0.88)
    try:
        ref = await agent.chat_json(
            [
                {"role": "system", "content": "你是四六级命题与阅卷专家，只输出合法 JSON。"},
                {
                    "role": "user",
                    "content": (
                        "根据下面的写作题与翻译题，分别生成一份高质量参考范文/参考译文。\n"
                        "只返回 JSON：{\"writing_reference\":\"...\",\"translation_reference\":\"...\"}。\n\n"
                        f"写作题：{paper.get('writing', {}).get('prompt', '')}\n"
                        f"翻译题：{paper.get('translation', {}).get('prompt', '')}\n"
                        f"答案材料（可能为空）：{answer_context[:12000]}"
                    ),
                },
            ],
            max_tokens=8000,
        )
        if ref.get("writing_reference"):
            paper["writing"]["reference_answer"] = str(ref["writing_reference"])
        if ref.get("translation_reference"):
            paper["translation"]["reference_answer"] = str(ref["translation_reference"])
    except Exception:
        pass
    await _progress(progress, "AI 润色完成", 0.96)


async def ocr_scanned_pdf(
    agent: AIAgentClient,
    pdf: Path,
    *,
    progress: Progress | None = None,
) -> str:
    images = extract_pdf_page_images(pdf)
    pages = [(i + 1, img) for i, img in enumerate(images) if img]
    if not pages:
        return ""
    chunks: list[str] = []
    for start in range(0, len(pages), 2):
        batch = pages[start : start + 2]
        await _progress(
            progress,
            f"AI 识别答案 PDF {start + 1}-{min(start + 2, len(pages))}/{len(pages)}…",
            0.10 + 0.35 * (start / max(1, len(pages))),
        )
        try:
            text = await agent.vision_text(
                [img for _, img in batch],
                "请把这几页大学英语四六级答案解析完整转写为纯文本，"
                "保留题号、英文原文、中文解析和参考译文；不要总结，不要遗漏。",
                max_tokens=12000,
            )
            chunks.append(f"\n--- PDF pages {batch[0][0]}-{batch[-1][0]} ---\n{text}")
        except Exception:
            continue
    return "\n".join(chunks)


async def extract_answer_key_with_ai(
    agent: AIAgentClient,
    question_text: str,
    answer_text: str = "",
    progress: Progress | None = None,
) -> dict[int, str]:
    await _progress(progress, "AI 识别答案页…", 0.35)
    data = await agent.chat_json(
        [
            {
                "role": "system",
                "content": "你是四六级试卷结构化助手，只输出合法 JSON。",
            },
            {
                "role": "user",
                "content": (
                    "从下面的试卷与答案解析文本中提取客观题答案。"
                    '只返回 JSON：{"answers":{"1":"B","2":"A"}}，题号用字符串。'
                    "听力 1-25，阅读 26-55；不确定的题不要编造。\n\n"
                    f"试卷：{question_text[:30000]}\n\n答案页：{answer_text[:30000]}"
                ),
            },
        ],
        max_tokens=8000,
    )
    raw = data.get("answers") or {}
    out: dict[int, str] = {}
    for key, value in raw.items():
        try:
            number = int(str(key).strip())
            letter = str(value).strip().upper()[:1]
        except (TypeError, ValueError):
            continue
        if 1 <= number <= 55 and letter in "ABCDEFGHIJKLMNO":
            out[number] = letter
    return out


async def build_imported_paper(
    question_pdf: Path,
    *,
    title: str,
    level: str,
    duration_sec: int,
    audio_path: Path | None = None,
    answer_pdf: Path | None = None,
    agent: AIAgentClient | None = None,
    use_vision: bool = True,
    progress: Progress | None = None,
) -> tuple[dict[str, Any], Path | None]:
    await _progress(progress, "读取试卷 PDF…", 0.04)
    text = extract_pdf_text(question_pdf)
    answer_text = extract_pdf_text(answer_pdf) if answer_pdf else ""
    if use_vision and len(text.strip()) < 200 and agent and agent.available:
        text = await ocr_scanned_pdf(agent, question_pdf, progress=progress)
    if use_vision and answer_pdf and len(answer_text.strip()) < 80 and agent and agent.available:
        answer_text = await ocr_scanned_pdf(agent, answer_pdf, progress=progress)
    await _progress(progress, "解析题目与答案结构…", 0.45)
    audio_name = "listening" + (audio_path.suffix if audio_path else ".mp3")
    try:
        paper = parse_cet_text(
            text,
            title=title,
            level=level,
            duration_sec=duration_sec,
            audio_name=audio_name,
            answer_text=answer_text,
        )
    except ValueError:
        if not agent or not agent.available:
            raise
        answers = await extract_answer_key_with_ai(
            agent, text, answer_text, progress=progress
        )
        paper = parse_cet_text(
            text,
            title=title,
            level=level,
            duration_sec=duration_sec,
            audio_name=audio_name,
            answer_text=answer_text,
            answers_override=answers,
        )
    paper["import_meta"] = {
        "question_pdf": question_pdf.name,
        "answer_pdf": answer_pdf.name if answer_pdf else "",
        "audio": audio_path.name if audio_path else "",
        "imported_at": now_iso(),
    }
    if agent and agent.available:
        await enrich_with_ai(
            agent,
            paper,
            answer_context=answer_text,
            progress=progress,
        )
    await _progress(progress, "生成试卷 JSON…", 0.98)
    return paper, answer_pdf
