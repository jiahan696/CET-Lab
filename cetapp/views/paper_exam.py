from __future__ import annotations

import asyncio
import re
import time
import traceback
from datetime import datetime
from typing import TYPE_CHECKING, Any

import flet as ft

from flet_audio import Audio, AudioState

from ..exam_service import finalize_paper_exam
from ..paperlib import (
    SECTION_LABELS,
    SECTION_MAX,
    paper_questions,
    score_paper,
)
from ..scoring import remaining_seconds, session_elapsed
from ..theme import (
    BLUSH,
    DANGER,
    DANGER_BG,
    FAINT,
    INDIGO,
    INDIGO_LIGHT,
    INK,
    INK_SOFT,
    LINE,
    LINE_SOFT,
    MINT,
    MUTED,
    SAND,
    SKY,
    SUCCESS,
    SUCCESS_BG,
    TEAL,
    TEAL_DARK,
    TEAL_LIGHT,
    WARNING,
    WARNING_BG,
    WHITE,
    action_button,
    body,
    divider,
    empty_state,
    eyebrow,
    frosted_panel,
    glass_card,
    heading,
    icon_box,
    pill,
    progress_track,
    selectable_text,
    text_action,
)
from ..utils import fmt_clock, fmt_duration, fmt_score, now_iso, uid
from .qcomponents import material_block, option_item

_PARAGRAPH_END = re.compile(r'[.!?]["”’\)]?$')
_LETTER_START = re.compile(r"^\s*([A-Z])\)\s*")


def format_reading_material(material: str, *, lettered: bool = False) -> str:
    """Rebuild paragraphs from pypdf's hard-wrapped lines and indent them.

    PDF text extraction produces one visual line per newline, not one paragraph
    per newline.  Section B is split by its A)/B)/... labels; other passages
    are split where a short line ends with sentence punctuation.  Each rebuilt
    paragraph starts with two full-width spaces so it reads like Chinese
    typography instead of a flush-left wall of text.
    """
    text = (material or "").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return ""
    indent = "\u3000\u3000"
    blocks: list[str] = []

    def clean(value: str) -> str:
        return re.sub(r"\s*\n\s*", " ", value).strip()

    if lettered:
        parts = re.split(r"(?m)(?=^\s*[A-Z]\)\s)", text)
        for part in parts:
            part = clean(part)
            if part:
                blocks.append(indent + part)
    elif "\n\n" in text:
        for part in re.split(r"\n\s*\n", text):
            part = clean(part)
            if part:
                blocks.append(indent + part)
    else:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        buffer: list[str] = []
        for line in lines:
            buffer.append(line)
            if len(line) <= 105 and _PARAGRAPH_END.search(line):
                blocks.append(indent + clean(" ".join(buffer)))
                buffer = []
        if buffer:
            blocks.append(indent + clean(" ".join(buffer)))
    return "\n\n".join(blocks)


def full_paragraph_bank(passage: dict[str, Any]) -> list[dict[str, str]]:
    """Use a complete first sentence for Section B hints.

    Imported JSON may contain a shortened hint in ``bank``.  The full paragraph
    is still available in ``material``; use its first complete sentence instead
    of an artificial ``...`` truncation, and keep the full paragraph as tooltip.
    """
    bank = passage.get("bank") or []
    if not bank:
        return []
    material = passage.get("material", "") or ""
    full: dict[str, str] = {}
    pattern = re.compile(
        r"(?ms)^\s*([A-Z])\)\s*(.*?)(?=^\s*[A-Z]\)\s|\Z)"
    )
    for match in pattern.finditer(material):
        text = re.sub(r"\s+", " ", match.group(2)).strip()
        if text:
            full[match.group(1)] = text
    result: list[dict[str, str]] = []
    for item in bank:
        key = str(item.get("key", ""))
        full_text = full.get(key, str(item.get("text", "") or ""))
        match = re.match(r"(.+?[.!?])(?:\s|$)", full_text, re.S)
        hint = match.group(1).strip() if match else full_text.strip()
        result.append({"key": key, "text": hint, "full_text": full_text})
    return result


if TYPE_CHECKING:
    from ..app import CETApp


SECTION_ICONS = {
    "writing": ft.Icons.EDIT_NOTE_ROUNDED,
    "listening": ft.Icons.HEADPHONES_ROUNDED,
    "reading": ft.Icons.MENU_BOOK_ROUNDED,
    "translation": ft.Icons.TRANSLATE_ROUNDED,
}


class PaperExamView:
    def __init__(self, app: "CETApp") -> None:
        self.app = app
        self.store = app.store
        self.library = app.library
        self.session = self.store.active_exam
        self.paper: dict[str, Any] | None = None
        if self.session and self.session.get("paper_id"):
            self.paper = self.library.get(self.session["paper_id"])
        if self.paper is None:
            self.session = None
        self.active = bool(self.session and self.paper)
        self.full_screen = self.active
        self._alive = self.active
        self._timer_started = False
        self._submitting = False
        self._last_text_save = 0.0
        self.audio: Audio | None = None
        self._audio_registered = False
        self._audio_started = False
        self._audio_duration_ms = 0
        self._audio_bar: ft.ProgressBar | None = None
        self._audio_position_text: ft.Text | None = None
        self._audio_duration_text: ft.Text | None = None
        self._audio_status_text: ft.Text | None = None
        self._timer_text: ft.Text | None = None
        self._timer_chip: ft.Container | None = None
        self._tabs_host: ft.Container | None = None
        self._content_host: ft.Container | None = None
        self._writing_count: ft.Text | None = None
        self._translation_count: ft.Text | None = None
        self._reading_question_hosts: dict[str, ft.Container] = {}
        try:
            self._layout_compact = float(app.page.width or 0) < 900
        except Exception:
            self._layout_compact = False

    # ------------------------------------------------------------------ build
    def build(self) -> ft.Control:
        if self.active and self.paper:
            self.full_screen = True
            self._alive = True
            control = self._active_screen()
            if not self._timer_started:
                self._timer_started = True
                self.app.page.run_task(self._timer_loop)
            return control
        self.full_screen = False
        return self._selection_screen()

    # --------------------------------------------------------------- selection
    def _selection_screen(self) -> ft.Control:
        papers = self.library.papers
        header = ft.Row(
            [
                ft.Container(
                    width=34,
                    height=34,
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.55, WHITE),
                    border=ft.Border.all(1, LINE_SOFT),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=17, color=INK_SOFT),
                    on_click=lambda _e: self.app.navigate("home"),
                    ink=True,
                ),
                ft.Column(
                    [
                        eyebrow("EXAM CENTER · 全真考场"),
                        heading("全真模拟考试", size=26),
                        body("选择一套试卷进入考场。导入新试卷后可在这里开始。", size=12),
                    ],
                    spacing=0,
                    expand=True,
                ),
                ft.Row(
                    [
                        action_button(
                            "导入试卷",
                            icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                            height=38,
                            font_size=11.5,
                            on_click=lambda: self.app.navigate("import"),
                        ),
                        action_button(
                            "AI 设置",
                            variant="secondary",
                            icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                            height=38,
                            font_size=11,
                            on_click=self.app.show_ai_settings,
                        ),
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        if not papers:
            return ft.Column(
                [
                    header,
                    glass_card(
                        empty_state(
                            "还没有试卷",
                            "上传真题 PDF、答案 PDF 和听力音频，AI 会生成一套可作答的试卷。",
                            icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                            action=action_button(
                                "导入第一套试卷",
                                icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                                on_click=lambda: self.app.navigate("import"),
                            ),
                        ),
                        padding=16,
                    ),
                ],
                spacing=16,
            )
        cards = [self._paper_card(p) for p in papers]
        return ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [
                            pill("选择题库", icon=ft.Icons.LIBRARY_BOOKS_ROUNDED, bg=TEAL_LIGHT, fg=TEAL_DARK),
                            heading("选择一套试卷，开始计时。", size=30),
                            body(
                                "写作 → 听力 → 阅读 → 翻译。听力进入后自动播放且不可暂停；"
                                "阅读为左原文、右全部题目的双栏布局；写作与翻译交卷后由 AI 评分。",
                                size=12.5,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.only(bottom=4),
                ),
                ft.ResponsiveRow(cards, spacing=14, run_spacing=14),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=14, color=FAINT),
                        ft.Text(
                            "导入试卷的音频与 JSON 均保存在本地；不会上传到除 AI 接口以外的服务。",
                            size=10.5,
                            color=FAINT,
                        ),
                    ],
                    spacing=6,
                ),
            ],
            spacing=16,
        )

    def _paper_card(self, paper: dict[str, Any]) -> ft.Control:
        meta = paper.get("paper", {})
        pid = meta.get("id", "")
        is_builtin = bool(paper.get("_builtin"))
        listening = sum(
            len(s.get("questions", []))
            for s in paper.get("listening", {}).get("sections", [])
        )
        reading = sum(
            len(p.get("questions", []))
            for p in paper.get("reading", {}).get("passages", [])
        )
        audio = self.library.audio_path(paper)
        title = meta.get("title", "未命名试卷")
        created = str(meta.get("created_at", ""))[:10]
        actions = [
            action_button(
                "开始考试",
                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                height=38,
                font_size=11.5,
                on_click=lambda _e=None, p=paper: self._start_paper(p),
            )
        ]
        if not is_builtin:
            actions.insert(
                0,
                text_action(
                    "删除",
                    lambda p=paper: self._delete_paper(p),
                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                    color=FAINT,
                    size=10,
                ),
            )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(
                                ft.Icons.DESCRIPTION_ROUNDED,
                                color=TEAL if is_builtin else INDIGO,
                                bg=TEAL_LIGHT if is_builtin else INDIGO_LIGHT,
                                size=42,
                                icon_size=19,
                                radius=13,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        title,
                                        size=15,
                                        weight=ft.FontWeight.W_700,
                                        color=INK,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        f"{meta.get('level', 'CET-4')} · {int(meta.get('duration_sec', 7500)) // 60} 分钟"
                                        + (f" · {created}" if created else ""),
                                        size=9.5,
                                        color=FAINT,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Row(
                        [
                            pill("内置示例" if is_builtin else "用户导入", bg=TEAL_LIGHT if is_builtin else SKY, fg=TEAL_DARK if is_builtin else INDIGO, size=9),
                            pill(f"听力 {listening}", bg="#EEF5F2", fg=SUCCESS, size=9),
                            pill(f"阅读 {reading}", bg=INDIGO_LIGHT, fg=INDIGO, size=9),
                            pill("含音频" if audio else "无音频", bg=SAND if audio else "#F3F0EA", fg=WARNING if audio else FAINT, size=9),
                        ],
                        spacing=6,
                        wrap=True,
                        run_spacing=6,
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                f"写作 + 翻译 AI 评分 · {listening + reading} 道客观题",
                                size=10,
                                color=MUTED,
                                expand=True,
                            ),
                            *actions,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=12,
            ),
            padding=18,
            col={"xs": 12, "md": 6},
            fill=0.64,
        )

    def _delete_paper(self, paper: dict[str, Any]) -> None:
        pid = paper.get("paper", {}).get("id", "")
        title = paper.get("paper", {}).get("title", "")

        def do_delete() -> None:
            self.library.delete_imported(pid)
            self.app.render()
            self.app.notify(f"已删除试卷：{title}", "success")

        self.app.confirm(
            "删除这套试卷？",
            f"将从本地删除「{title}」的 JSON 与音频文件，历史成绩不受影响。",
            confirm_label="删除试卷",
            danger=True,
            on_confirm=do_delete,
        )

    def _start_paper(self, paper: dict[str, Any]) -> None:
        meta = paper.get("paper", {})
        duration = int(meta.get("duration_sec", 125 * 60))
        now = time.time()
        session = {
            "id": uid(),
            "paper_id": meta.get("id", ""),
            "paper_title": meta.get("title", ""),
            "level": meta.get("level", "CET-4"),
            "started_at": now_iso(),
            "started_ts": now,
            "duration_sec": duration,
            "deadline_ts": now + duration,
            "section": "writing",
            "answers": {},
            "text_answers": {"writing": "", "translation": ""},
            "marked": [],
            "listening_index": 0,
            "reading_passage": 0,
            "saved_at": now_iso(),
        }
        self.session = session
        self.paper = paper
        self.active = True
        self.full_screen = True
        self._alive = True
        self._timer_started = False
        self.store.set_active_exam(session)
        self.app.render()
        self.app.notify("考试开始，写作计时已启动。", "info")

    # ------------------------------------------------------------------ active
    def _active_screen(self) -> ft.Control:
        self.full_screen = True
        self._ensure_audio()
        self._tabs_host = ft.Container(content=self._section_tabs())
        self._content_host = ft.Container(content=self._section_content(), expand=True)
        header = self._header()
        screen = ft.Column(
            [
                ft.Container(content=header, padding=ft.Padding.only(left=18, right=18, top=12)),
                ft.Container(
                    content=self._tabs_host,
                    padding=ft.Padding.only(left=18, right=18, top=10),
                ),
                ft.Container(
                    content=self._content_host,
                    expand=True,
                    padding=ft.Padding.only(left=18, right=18, top=10, bottom=18),
                ),
            ],
            spacing=0,
            expand=True,
        )
        if self._section_key() == "listening":
            self.app.page.run_task(self._play_audio_once)
        return screen

    def _section_key(self) -> str:
        return (self.session or {}).get("section", "writing")

    def _header(self) -> ft.Control:
        remaining = remaining_seconds(self.session) if self.session else 0
        self._timer_text = ft.Text(
            fmt_clock(remaining),
            size=16,
            weight=ft.FontWeight.W_800,
            color=DANGER if remaining < 300 else INK,
            no_wrap=True,
        )
        self._timer_chip = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.TIMER_ROUNDED, size=14, color=DANGER if remaining < 300 else TEAL),
                    self._timer_text,
                ],
                spacing=5,
                tight=True,
            ),
            padding=ft.Padding.symmetric(horizontal=9, vertical=7),
            border_radius=12,
            bgcolor=DANGER_BG if remaining < 300 else TEAL_LIGHT,
            border=ft.Border.all(1, "#F0C9CF" if remaining < 300 else "#C9E3E0"),
        )
        paper_title = self.paper.get("paper", {}).get("title", "全真模考") if self.paper else "全真模考"
        title = ft.Column(
            [
                ft.Text("全真模考", size=15, weight=ft.FontWeight.W_700, color=INK, no_wrap=True),
                ft.Text(
                    paper_title,
                    size=9.5,
                    color=FAINT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=1,
            expand=True,
        )
        return glass_card(
            ft.Row(
                [
                    ft.Container(
                        width=34,
                        height=34,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.55, WHITE),
                        border=ft.Border.all(1, LINE_SOFT),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=17, color=INK_SOFT),
                        on_click=lambda _e: self._confirm_exit(),
                        ink=True,
                    ),
                    title,
                    self._timer_chip,
                    action_button(
                        "交卷",
                        height=36,
                        font_size=11.5,
                        on_click=self._confirm_submit,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            radius=20,
            fill=0.66,
        )

    def _section_tabs(self) -> ft.Control:
        compact = self.app.page.width < 700
        tabs = []
        for key in ("writing", "listening", "reading", "translation"):
            active = key == self._section_key()
            if key == "writing":
                done = bool(self.session.get("text_answers", {}).get("writing", "").strip())
                detail = "已写" if done else "30 min"
            elif key == "listening":
                count = len(self._listening_questions())
                done = sum(1 for q in self._listening_questions() if self._answer(q["id"]))
                detail = "无听力" if count == 0 else f"{done}/{count}"
            elif key == "reading":
                count = len(self._reading_questions())
                done = sum(1 for q in self._reading_questions() if self._answer(q["id"]))
                detail = f"{done}/{count}"
            else:
                done = bool(self.session.get("text_answers", {}).get("translation", "").strip())
                detail = "已译" if done else "30 min"
            tabs.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(SECTION_ICONS[key], size=14, color=WHITE if active else TEAL_DARK),
                            ft.Text(
                                SECTION_LABELS[key],
                                size=11.5,
                                weight=ft.FontWeight.W_700,
                                color=WHITE if active else INK_SOFT,
                                no_wrap=True,
                            ),
                            ft.Container(expand=True),
                            *(
                                [
                                    ft.Text(
                                        detail,
                                        size=9,
                                        color="#DDF2ED" if active else FAINT,
                                        no_wrap=True,
                                    )
                                ]
                                if not compact
                                else []
                            ),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8 if compact else 11, vertical=9),
                    bgcolor=TEAL if active else ft.Colors.with_opacity(0.42, WHITE),
                    border=ft.Border.all(1, "#B9DED8" if active else LINE_SOFT),
                    border_radius=13,
                    expand=True,
                    on_click=lambda _e, k=key: self._switch_section(k),
                    ink=True,
                )
            )
        return ft.Row(tabs, spacing=8)

    def _switch_section(self, key: str) -> None:
        if not self.session or key not in SECTION_LABELS:
            return
        self._save(touch_ui=False)
        self.session["section"] = key
        self._save(touch_ui=False)
        if self._tabs_host is not None:
            self._tabs_host.content = self._section_tabs()
        if self._content_host is not None:
            self._content_host.content = self._section_content()
        if key == "listening":
            self.app.page.run_task(self._play_audio_once)
        try:
            self.app.page.update()
        except Exception:
            pass

    def _section_content(self) -> ft.Control:
        key = self._section_key()
        if key == "listening":
            return self._listening_content()
        if key == "reading":
            return self._reading_content()
        if key == "translation":
            return self._translation_content()
        return self._writing_content()

    # ------------------------------------------------------------------ shared
    def _answer(self, qid: str) -> list[str]:
        if not self.session:
            return []
        return list((self.session.get("answers", {}) or {}).get(qid, []) or [])

    def _set_answer(self, qid: str, choices: list[str]) -> None:
        if not self.session:
            return
        answers = self.session.setdefault("answers", {})
        if choices:
            answers[qid] = sorted(choices)
        else:
            answers.pop(qid, None)
        self._save(touch_ui=False)

    def _save(self, *, touch_ui: bool = True) -> None:
        if not self.session:
            return
        self.session["saved_at"] = now_iso()
        self.store.set_active_exam(self.session)
        if touch_ui:
            try:
                self.app.page.update()
            except Exception:
                pass

    def _refresh_tabs(self) -> None:
        if self._tabs_host is not None:
            self._tabs_host.content = self._section_tabs()

    # ------------------------------------------------------------------ writing
    def _writing_content(self) -> ft.Control:
        task = (self.paper or {}).get("writing", {})
        text = self.session.get("text_answers", {}).get("writing", "")
        self._writing_count = ft.Text(f"{len(text.split())} words", size=10, color=FAINT)
        editor = ft.TextField(
            value=text,
            multiline=True,
            min_lines=16,
            max_lines=24,
            border_radius=16,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.46, WHITE),
            border_color="#D8E4EE",
            focused_border_color=TEAL,
            color=INK,
            text_size=13.5,
            hint_text="在这里完成写作，内容会自动保存…",
            on_change=lambda e: self._on_text_change("writing", e.control.value),
        )
        left = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.EDIT_NOTE_ROUNDED, color=TEAL, bg=TEAL_LIGHT, size=38, icon_size=18, radius=12),
                            ft.Column(
                                [
                                    ft.Text("Part I Writing", size=16, weight=ft.FontWeight.W_700, color=INK),
                                    body(
                                        f"{task.get('word_limit', [120, 180])[0]}-{task.get('word_limit', [120, 180])[1]} words · 30 minutes",
                                        size=10,
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=10,
                    ),
                    divider(),
                    selectable_text(
                        task.get("prompt", ""),
                        size=14,
                        color=INK,
                        line_height=1.7,
                        on_select=lambda text: self.app.translate_selection(
                            text, source="写作题目"
                        ),
                    ),
                    frosted_panel(
                        ft.Text(
                            "交卷后由 AI 按 CET 写作 15 分制评分，再折算为 106.5 分。",
                            size=10.5,
                            color=INK_SOFT,
                            style=ft.TextStyle(height=1.5),
                        ),
                        padding=11,
                        fill=0.42,
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
        right = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("写作答题区", size=13, weight=ft.FontWeight.W_700, color=INK),
                            ft.Container(expand=True),
                            self._writing_count,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    editor,
                ],
                spacing=10,
                expand=True,
            ),
            padding=18,
            expand=True,
        )
        if self.app.page.width >= 900:
            layout_control: ft.Control = ft.Row([left, right], expand=True, spacing=14, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        else:
            left.height = 360
            layout_control = ft.Column([left, ft.Container(content=right, height=420)], scroll=ft.ScrollMode.AUTO, expand=True, spacing=14)
        return layout_control

    def _on_text_change(self, kind: str, value: str) -> None:
        if not self.session:
            return
        self.session.setdefault("text_answers", {})[kind] = value
        if kind == "writing" and self._writing_count is not None:
            self._writing_count.value = f"{len(value.split())} words"
        if kind == "translation" and self._translation_count is not None:
            self._translation_count.value = f"{len(value.split())} words"
        now = time.monotonic()
        if now - self._last_text_save > 2.0:
            self._last_text_save = now
            self._save(touch_ui=False)
        self._refresh_tabs()
        try:
            self.app.page.update()
        except Exception:
            pass

    # --------------------------------------------------------------- translation
    def _translation_content(self) -> ft.Control:
        task = (self.paper or {}).get("translation", {})
        text = self.session.get("text_answers", {}).get("translation", "")
        self._translation_count = ft.Text(f"{len(text.split())} words", size=10, color=FAINT)
        editor = ft.TextField(
            value=text,
            multiline=True,
            min_lines=14,
            max_lines=22,
            border_radius=16,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.46, WHITE),
            border_color="#D8E4EE",
            focused_border_color=TEAL,
            color=INK,
            text_size=13.5,
            hint_text="在这里完成全文翻译，内容会自动保存…",
            on_change=lambda e: self._on_text_change("translation", e.control.value),
        )
        left = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.TRANSLATE_ROUNDED, color=WARNING, bg=SAND, size=38, icon_size=18, radius=12),
                            ft.Column(
                                [
                                    ft.Text("Part IV Translation", size=16, weight=ft.FontWeight.W_700, color=INK),
                                    body("30 minutes · 全文翻译", size=10),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=10,
                    ),
                    divider(),
                    selectable_text(
                        task.get("prompt", ""),
                        size=14,
                        color=INK,
                        line_height=1.8,
                        on_select=lambda text: self.app.translate_selection(
                            text, source="翻译原文"
                        ),
                    ),
                    frosted_panel(
                        ft.Text(
                            "交卷后由 AI 按 CET 翻译 15 分制评分，再折算为 106.5 分。译文会自动保存。",
                            size=10.5,
                            color=INK_SOFT,
                            style=ft.TextStyle(height=1.5),
                        ),
                        padding=11,
                        fill=0.42,
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
        right = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("翻译答题区", size=13, weight=ft.FontWeight.W_700, color=INK),
                            ft.Container(expand=True),
                            self._translation_count,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    editor,
                ],
                spacing=10,
                expand=True,
            ),
            padding=18,
            expand=True,
        )
        if self.app.page.width >= 900:
            layout_control: ft.Control = ft.Row([left, right], expand=True, spacing=14, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        else:
            left.height = 340
            layout_control = ft.Column([left, ft.Container(content=right, height=420)], scroll=ft.ScrollMode.AUTO, expand=True, spacing=14)
        return layout_control

    # ---------------------------------------------------------------- listening
    def _listening_questions(self) -> list[dict[str, Any]]:
        if not self.paper:
            return []
        return [
            q
            for section in self.paper.get("listening", {}).get("sections", [])
            for q in section.get("questions", [])
        ]

    def _listening_index(self) -> int:
        if not self.session:
            return 0
        total = len(self._listening_questions())
        return max(0, min(total - 1, int(self.session.get("listening_index", 0) or 0)))

    def _listening_content(self) -> ft.Control:
        qs = self._listening_questions()
        if not qs:
            return glass_card(empty_state("没有听力题", "这套试卷未包含听力题目。", icon=ft.Icons.HEADPHONES_ROUNDED), padding=16)
        audio_bar = self._audio_bar_control()
        card = glass_card(self._listening_question_body(), padding=22, expand=True)
        sidebar = glass_card(self._listening_sidebar(), padding=18, width=280)
        if self.app.page.width >= 1000:
            layout_control = ft.Row([card, sidebar], expand=True, spacing=14, vertical_alignment=ft.CrossAxisAlignment.START)
        else:
            layout_control = ft.Column([card, sidebar], spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)
        return ft.Column([audio_bar, layout_control], spacing=12, expand=True)

    def _listening_question_body(self) -> ft.Control:
        qs = self._listening_questions()
        idx = self._listening_index()
        q = qs[idx]
        answer = self._answer(self._global_qid(q))
        qid = self._global_qid(q)
        options = ft.Column(
            [
                option_item(
                    chr(65 + i),
                    text,
                    selected=chr(65 + i) in answer,
                    on_click=lambda key, qid=qid: self._choose_single(qid, key),
                )
                for i, text in enumerate(q.get("options", []))
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        return ft.Column(
            [
                ft.Row(
                    [
                        pill("听力理解", bg=TEAL_LIGHT, fg=TEAL_DARK, size=10),
                        pill("单选题", bg=SKY, fg=INDIGO, size=10),
                        ft.Container(expand=True),
                        ft.Text(f"{idx + 1:02d} / {len(qs):02d}", size=10, color=FAINT),
                    ],
                    spacing=7,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                divider(),
                ft.Text(
                    q.get("question") or "请根据录音内容选择最佳答案。",
                    size=17,
                    weight=ft.FontWeight.W_700,
                    color=INK,
                    style=ft.TextStyle(height=1.5),
                ),
                ft.Text("听力音频播放中不可暂停，请边听边作答。", size=10.5, color=FAINT),
                options,
                divider(),
                ft.Row(
                    [
                        text_action("上一题", lambda: self._jump_listening(-1), icon=ft.Icons.NAVIGATE_BEFORE_ROUNDED, size=11),
                        ft.Container(expand=True),
                        text_action("下一题", lambda: self._jump_listening(1), icon=ft.Icons.ARROW_FORWARD_ROUNDED, size=11),
                    ]
                ),
            ],
            spacing=13,
        )

    def _listening_sidebar(self) -> ft.Control:
        qs = self._listening_questions()
        answered = sum(1 for q in qs if self._answer(self._global_qid(q)))
        current = self._listening_index()
        buttons = []
        for i, q in enumerate(qs):
            qid = self._global_qid(q)
            has = bool(self._answer(qid))
            active = i == current
            buttons.append(
                ft.Container(
                    width=34,
                    height=31,
                    border_radius=9,
                    bgcolor=TEAL if active else ("#D8ECE7" if has else ft.Colors.with_opacity(0.45, WHITE)),
                    border=ft.Border.all(1, TEAL_DARK if active else ("#B8DCD4" if has else LINE_SOFT)),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        str(i + 1),
                        size=10.5,
                        color=WHITE if active else (TEAL_DARK if has else MUTED),
                        weight=ft.FontWeight.W_700 if active or has else ft.FontWeight.W_500,
                    ),
                    on_click=lambda _e, idx=i: self._jump_listening_to(idx),
                    ink=True,
                )
            )
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("答题卡", size=16, weight=ft.FontWeight.W_700, color=INK),
                        ft.Container(expand=True),
                        pill(f"{answered}/{len(qs)}", bg=TEAL_LIGHT, fg=TEAL_DARK, size=10),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        self._legend(TEAL, "已答"),
                        self._legend("#DCE7EF", "未答"),
                    ],
                    spacing=10,
                ),
                divider(),
                ft.Row(buttons, spacing=6, run_spacing=6, wrap=True),
                divider(),
                action_button(
                    "提交试卷",
                    icon=ft.Icons.FACT_CHECK_ROUNDED,
                    height=40,
                    font_size=12,
                    on_click=self._confirm_submit,
                ),
                ft.Text("听力音频不可暂停", size=9, color=FAINT, text_align=ft.TextAlign.CENTER),
            ],
            spacing=11,
        )

    def _legend(self, color: str, label: str) -> ft.Control:
        return ft.Row(
            [
                ft.Container(width=8, height=8, border_radius=3, bgcolor=color),
                ft.Text(label, size=9, color=MUTED),
            ],
            spacing=4,
            tight=True,
        )

    def _choose_single(self, qid: str, key: str) -> None:
        self._set_answer(qid, [key])
        if self._content_host is not None:
            self._content_host.content = self._section_content()
        self._refresh_tabs()
        try:
            self.app.page.update()
        except Exception:
            pass

    def _jump_listening(self, delta: int) -> None:
        self._jump_listening_to(self._listening_index() + delta)

    def _jump_listening_to(self, index: int) -> None:
        if not self.session:
            return
        qs = self._listening_questions()
        self.session["listening_index"] = max(0, min(len(qs) - 1, int(index)))
        self._save(touch_ui=False)
        if self._content_host is not None:
            self._content_host.content = self._section_content()
        self._refresh_tabs()
        try:
            self.app.page.update()
        except Exception:
            pass

    # ------------------------------------------------------------------ reading
    def _passages(self) -> list[dict[str, Any]]:
        return (self.paper or {}).get("reading", {}).get("passages", [])

    def _reading_passage_index(self) -> int:
        total = len(self._passages())
        if not total:
            return 0
        return max(0, min(total - 1, int(self.session.get("reading_passage", 0) or 0)))

    def _reading_questions(self) -> list[dict[str, Any]]:
        return [q for p in self._passages() for q in p.get("questions", [])]

    def _reading_content(self) -> ft.Control:
        passages = self._passages()
        if not passages:
            return glass_card(empty_state("没有阅读题", "这套试卷未包含阅读题目。", icon=ft.Icons.MENU_BOOK_ROUNDED), padding=16)
        idx = self._reading_passage_index()
        passage = passages[idx]
        selector = ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        p.get("title", f"Passage {i+1}"),
                        size=10.5,
                        color=WHITE if i == idx else INK_SOFT,
                        weight=ft.FontWeight.W_600,
                        no_wrap=True,
                    ),
                    padding=ft.Padding.symmetric(horizontal=11, vertical=7),
                    bgcolor=TEAL if i == idx else ft.Colors.with_opacity(0.42, WHITE),
                    border=ft.Border.all(1, "#B9DED8" if i == idx else LINE_SOFT),
                    border_radius=999,
                    on_click=lambda _e, n=i: self._select_passage(n),
                    ink=True,
                )
                for i, p in enumerate(passages)
            ],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
        )
        left = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(passage.get("title", "Reading"), size=15, weight=ft.FontWeight.W_700, color=INK),
                            ft.Container(expand=True),
                            pill("左原文 · 可上下滚动", bg=TEAL_LIGHT, fg=TEAL_DARK, size=9),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    divider(),
                    selectable_text(
                        format_reading_material(
                            passage.get("material", ""),
                            lettered=passage.get("display") == "paragraph_matching",
                        ),
                        size=13.5,
                        color=INK_SOFT,
                        line_height=1.8,
                        on_select=lambda text, passage=passage: self.app.translate_selection(
                            text,
                            context=passage.get("material", "")[:1500],
                            source=passage.get("title", "阅读原文"),
                        ),
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
        compact = self.app.page.width < 900
        bank_panel = self._bank_panel(passage)
        question_blocks = [
            self._reading_question_block(q, passage)
            for q in passage.get("questions", [])
        ]
        right_header = ft.Row(
            [
                ft.Text(
                    f"{passage.get('title', 'Reading')} · 全部题目",
                    size=15,
                    weight=ft.FontWeight.W_700,
                    color=INK,
                ),
                ft.Container(expand=True),
                pill(
                    "右题目 · 可上下滚动",
                    bg=INDIGO_LIGHT,
                    fg=INDIGO,
                    size=9,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        # The bank sits at the top of the question scroll, not in the passage
        # pane.  Keeping it inside the scroll gives the questions the full
        # remaining height instead of permanently squeezing them below it.
        right_body = ft.Column(
            [
                right_header,
                divider(),
                ft.Column(
                    [
                        bank_panel,
                        divider(),
                        *question_blocks,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            spacing=10,
            expand=True,
        )
        right = glass_card(
            right_body,
            padding=18,
            expand=True,
        )
        if not compact:
            panes: ft.Control = ft.Row([left, right], expand=True, spacing=14, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        else:
            left.height = 320
            panes = ft.Column(
                [
                    left,
                    ft.Container(content=right, expand=True),
                ],
                expand=True,
                spacing=12,
            )
        return ft.Column([selector, panes], spacing=10, expand=True)

    def _bank_panel(self, passage: dict[str, Any]) -> ft.Control:
        is_paragraph = passage.get("display") == "paragraph_matching"
        bank = (
            full_paragraph_bank(passage)
            if is_paragraph
            else (passage.get("bank") or [])
        )
        if not bank:
            return ft.Container()
        if is_paragraph:
            title = "段落提示"
            en = "PARAGRAPH BANK"
            hint = "完整首句 · 悬停看全段"
            col = {"xs": 12, "sm": 6, "lg": 4}
            text_size = 13
        else:
            title = "选词填空词库"
            en = "WORD BANK"
            hint = "从 A-O 中为每个空选择单词"
            col = {"xs": 6, "sm": 4, "lg": 4}
            text_size = 13
        entries: list[ft.Control] = []
        for item in bank:
            key = str(item.get("key", ""))
            text = str(item.get("text", "") or "")
            entries.append(
                ft.Container(
                    col=col,
                    content=ft.Row(
                        [
                            ft.Container(
                                width=24,
                                height=24,
                                border_radius=7,
                                bgcolor=TEAL_LIGHT if not is_paragraph else INDIGO_LIGHT,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text(
                                    key,
                                    size=10.5,
                                    color=TEAL_DARK if not is_paragraph else INDIGO,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ),
                            ft.Text(
                                text,
                                size=text_size,
                                color=INK_SOFT,
                                weight=ft.FontWeight.W_500,
                                max_lines=None if is_paragraph else 2,
                                overflow=(
                                    None
                                    if is_paragraph
                                    else ft.TextOverflow.ELLIPSIS
                                ),
                                tooltip=(
                                    item.get("full_text")
                                    if is_paragraph and item.get("full_text")
                                    else None
                                ),
                                style=ft.TextStyle(height=1.45),
                                expand=True,
                            ),
                        ],
                        spacing=7,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=7),
                    bgcolor=ft.Colors.with_opacity(0.36, WHITE),
                    border=ft.Border.all(1, LINE_SOFT),
                    border_radius=10,
                )
            )
        header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(title, size=12, weight=ft.FontWeight.W_700, color=INK),
                        ft.Text(en, size=8, color=FAINT, weight=ft.FontWeight.W_700),
                    ],
                    spacing=0,
                ),
                ft.Container(expand=True),
                ft.Text(hint, size=10, color=FAINT, no_wrap=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return frosted_panel(
            ft.Column(
                [
                    header,
                    ft.ResponsiveRow(entries, spacing=6, run_spacing=6),
                ],
                spacing=8,
            ),
            padding=11,
            fill=0.42,
        )

    def _reading_question_block(self, q: dict[str, Any], passage: dict[str, Any]) -> ft.Control:
        qid = self._global_qid(q)
        answer = self._answer(qid)
        host = ft.Container(content=self._reading_question_body(q, passage))
        self._reading_question_hosts[qid] = host
        return host

    def _reading_question_body(self, q: dict[str, Any], passage: dict[str, Any]) -> ft.Control:
        qid = self._global_qid(q)
        answer = self._answer(qid)
        number = q.get("number", 0)
        options = q.get("options", [])
        marked = qid in (self.session.get("marked", []) if self.session else [])
        controls: list[ft.Control] = [
            ft.Row(
                [
                    ft.Container(
                        width=28,
                        height=28,
                        border_radius=8,
                        bgcolor=TEAL_LIGHT,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(str(number), size=10, color=TEAL_DARK, weight=ft.FontWeight.W_700),
                    ),
                    ft.Text(
                        q.get("question", ""),
                        size=12.5,
                        color=INK,
                        weight=ft.FontWeight.W_600,
                        selectable=True,
                        on_selection_change=lambda e: self.app.translate_selection(e.selected_text, source=f"阅读第 {number} 题"),
                        expand=True,
                        style=ft.TextStyle(height=1.5),
                    ),
                    ft.Container(
                        width=28,
                        height=28,
                        border_radius=8,
                        bgcolor=WARNING_BG if marked else ft.Colors.with_opacity(0.35, WHITE),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(
                            ft.Icons.BOOKMARK_ROUNDED if marked else ft.Icons.BOOKMARK_BORDER_ROUNDED,
                            size=14,
                            color=WARNING if marked else FAINT,
                        ),
                        tooltip="取消标记" if marked else "标记本题",
                        on_click=lambda _e, qid=qid: self._toggle_mark(qid),
                        ink=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ]
        display = passage.get("display", "passage")
        if display in ("word_bank", "paragraph_matching") or len(options) > 4:
            letter_bank = passage.get("bank") or [
                {"key": chr(65 + i), "text": ""} for i in range(len(options))
            ]
            letters = [b.get("key") for b in letter_bank if b.get("key")]
            selected = answer[0] if answer else ""
            controls.append(
                ft.Row(
                    [
                        ft.Container(
                            width=34,
                            height=30,
                            border_radius=8,
                            bgcolor=TEAL if key == selected else ft.Colors.with_opacity(0.45, WHITE),
                            border=ft.Border.all(1, TEAL_DARK if key == selected else LINE_SOFT),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(
                                key,
                                size=10,
                                color=WHITE if key == selected else MUTED,
                                weight=ft.FontWeight.W_700 if key == selected else ft.FontWeight.W_500,
                            ),
                            tooltip=(next((b.get("text", "") for b in letter_bank if b.get("key") == key), "") or key),
                            on_click=lambda _e, k=key: self._choose_reading(qid, k),
                            ink=True,
                        )
                        for key in letters
                    ],
                    spacing=5,
                    run_spacing=5,
                    wrap=True,
                )
            )
        else:
            controls.append(
                ft.Column(
                    [
                        option_item(
                            chr(65 + i),
                            text,
                            selected=chr(65 + i) in answer,
                            on_click=lambda key, qid=qid: self._choose_reading(qid, key),
                        )
                        for i, text in enumerate(options)
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                )
            )
        controls.append(divider())
        return ft.Column(controls, spacing=8)

    def _toggle_mark(self, qid: str) -> None:
        if not self.session:
            return
        marked = self.session.setdefault("marked", [])
        if qid in marked:
            marked.remove(qid)
        else:
            marked.append(qid)
        self._save(touch_ui=False)
        host = self._reading_question_hosts.get(qid)
        if host is not None:
            q = next(q for q in self._reading_questions() if self._global_qid(q) == qid)
            passage = next(
                p
                for p in self._passages()
                if any(self._global_qid(x) == qid for x in p.get("questions", []))
            )
            host.content = self._reading_question_body(q, passage)
        try:
            self.app.page.update()
        except Exception:
            pass

    def _select_passage(self, index: int) -> None:
        if not self.session:
            return
        self.session["reading_passage"] = index
        self._save(touch_ui=False)
        if self._content_host is not None:
            self._content_host.content = self._section_content()
        self._refresh_tabs()
        try:
            self.app.page.update()
        except Exception:
            pass

    def _choose_reading(self, qid: str, key: str) -> None:
        self._set_answer(qid, [key])
        host = self._reading_question_hosts.get(qid)
        if host is not None:
            q = next(q for q in self._reading_questions() if self._global_qid(q) == qid)
            passage = next(
                p
                for p in self._passages()
                if any(self._global_qid(x) == qid for x in p.get("questions", []))
            )
            host.content = self._reading_question_body(q, passage)
        self._refresh_tabs()
        try:
            self.app.page.update()
        except Exception:
            pass

    # -------------------------------------------------------------------- audio
    def _pause_audio(self) -> None:
        if self.audio is not None:
            self.app.page.run_task(self._pause_audio_async)

    async def _pause_audio_async(self) -> None:
        if self.audio is not None:
            try:
                await self.audio.pause()
            except Exception:
                pass

    def _audio_source(self) -> Path | None:
        if not self.paper:
            return None
        return self.library.audio_path(self.paper)

    def _ensure_audio(self) -> None:
        source = self._audio_source()
        if not source:
            return
        if self.audio is None:
            self.audio = Audio(
                src=str(source),
                autoplay=False,
                volume=0.9,
                on_duration_change=self._on_audio_duration,
                on_position_change=self._on_audio_position,
                on_state_change=self._on_audio_state,
            )
        if not self._audio_registered:
            self.app.page.services.append(self.audio)
            self._audio_registered = True

    def _audio_bar_control(self) -> ft.Control:
        self._audio_bar = progress_track(0, height=6, color=TEAL)
        self._audio_position_text = ft.Text("00:00", size=10, color=FAINT)
        self._audio_status_text = ft.Text(
            "进入听力后自动播放，播放期间不可暂停" if self._audio_source() else "本试卷未提供听力音频",
            size=10,
            color=WARNING if self._audio_source() else FAINT,
            weight=ft.FontWeight.W_600,
        )
        self._audio_duration_text = ft.Text(
            fmt_clock(self._audio_duration_ms / 1000) if self._audio_duration_ms else "--:--",
            size=10,
            color=FAINT,
        )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.HEADPHONES_ROUNDED, color=TEAL, bg=TEAL_LIGHT, size=34, icon_size=16, radius=10),
                            ft.Column(
                                [
                                    ft.Text("听力音频", size=12, weight=ft.FontWeight.W_700, color=INK),
                                    self._audio_status_text,
                                ],
                                spacing=0,
                                expand=True,
                            ),
                            self._audio_position_text,
                            ft.Text("/", size=10, color=FAINT),
                            self._audio_duration_text,
                            pill("不可暂停", bg=WARNING_BG, fg=WARNING, size=9),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._audio_bar,
                ],
                spacing=7,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            radius=16,
            fill=0.60,
        )

    async def _play_audio_once(self) -> None:
        self._ensure_audio()
        if self.audio is None or self._audio_started:
            return
        self._audio_started = True
        if self._audio_status_text is not None:
            self._audio_status_text.value = "听力播放中 · 不可暂停"
            self._audio_status_text.color = TEAL
            try:
                self.app.page.update()
            except Exception:
                pass
        try:
            await self.audio.play()
        except Exception as exc:
            self._audio_started = False
            if self._audio_status_text is not None:
                self._audio_status_text.value = f"音频播放失败：{exc}"
                self._audio_status_text.color = DANGER
                try:
                    self.app.page.update()
                except Exception:
                    pass

    def _on_audio_duration(self, e) -> None:
        duration = getattr(e, "duration", None)
        if duration is not None:
            self._audio_duration_ms = int(getattr(duration, "in_milliseconds", 0) or 0)
            if self._audio_duration_text is not None:
                self._audio_duration_text.value = fmt_clock(self._audio_duration_ms / 1000)
                try:
                    self._audio_duration_text.update()
                except Exception:
                    pass

    def _on_audio_position(self, e) -> None:
        position = int(getattr(e, "position", 0) or 0)
        if self._audio_bar is not None:
            self._audio_bar.value = (
                min(1.0, position / self._audio_duration_ms)
                if self._audio_duration_ms
                else 0
            )
        if self._audio_position_text is not None:
            self._audio_position_text.value = fmt_clock(position / 1000)
        try:
            if self._audio_bar is not None:
                self._audio_bar.update()
            if self._audio_position_text is not None:
                self._audio_position_text.update()
        except Exception:
            pass

    def _on_audio_state(self, e) -> None:
        state = getattr(e, "state", None)
        if self._audio_status_text is None:
            return
        if state == AudioState.PLAYING:
            self._audio_status_text.value = "听力播放中 · 不可暂停"
            self._audio_status_text.color = TEAL
        elif state == AudioState.COMPLETED:
            self._audio_status_text.value = "听力播放完毕"
            self._audio_status_text.color = SUCCESS
        elif state == AudioState.PAUSED:
            # There is deliberately no pause control; this is only a safety note.
            self._audio_status_text.value = "音频暂停"
        try:
            self._audio_status_text.update()
        except Exception:
            pass

    # ------------------------------------------------------------------ helpers
    def _global_qid(self, q: dict[str, Any]) -> str:
        if "id" in q and "::" in str(q["id"]):
            return str(q["id"])
        pid = (self.paper or {}).get("paper", {}).get("id", "")
        return f"{pid}::{q.get('id')}"

    # -------------------------------------------------------------------- timer
    async def _timer_loop(self) -> None:
        while self._alive and self.session and not self._submitting:
            remaining = remaining_seconds(self.session)
            if remaining <= 0:
                self._submit("timeout")
                break
            if self._timer_text is not None:
                self._timer_text.value = fmt_clock(remaining)
                danger = remaining < 300
                self._timer_text.color = DANGER if danger else INK
                if self._timer_chip is not None:
                    self._timer_chip.bgcolor = DANGER_BG if danger else TEAL_LIGHT
                    self._timer_chip.border = ft.Border.all(1, "#F0C9CF" if danger else "#C9E3E0")
                try:
                    self._timer_text.update()
                    if self._timer_chip is not None:
                        self._timer_chip.update()
                except Exception:
                    pass
            if int(remaining) % 15 == 0:
                self._save(touch_ui=False)
            await asyncio.sleep(1)

    # ------------------------------------------------------------------- submit
    def _confirm_submit(self) -> None:
        if not self.session or self._submitting:
            return
        objective = self._listening_questions() + self._reading_questions()
        unanswered = sum(1 for q in objective if not self._answer(self._global_qid(q)))
        text = self.session.get("text_answers", {})
        missing_text = []
        if not (text.get("writing") or "").strip():
            missing_text.append("写作")
        if not (text.get("translation") or "").strip():
            missing_text.append("翻译")
        notes = []
        if unanswered:
            notes.append(f"{unanswered} 道客观题未作答")
        if missing_text:
            notes.append("、".join(missing_text) + "未填写")
        message = "；".join(notes) if notes else "所有题目均已作答。"
        message += " 交卷后将调用 AI 评分写作与翻译，可能等待十几秒，之后不可修改。"
        self.app.confirm(
            "确认提交试卷？",
            message,
            confirm_label="确认交卷",
            cancel_label="继续答题",
            on_confirm=lambda: self._submit("manual"),
        )

    def _submit(self, completed_by: str) -> None:
        if not self.session or self._submitting:
            return
        self._submitting = True
        self._alive = False
        self.app.page.run_task(self._submit_async, completed_by)

    async def _none_result(self):
        return None

    async def _submit_async(self, completed_by: str) -> None:
        if not self.session or not self.paper:
            return
        self._save(touch_ui=False)
        status = ft.Text("正在交卷…", size=12, color=INK)
        bar = progress_track(0.15, height=7, color=TEAL)
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.with_opacity(0.98, WHITE),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Row(
                [
                    icon_box(ft.Icons.AUTO_AWESOME_ROUNDED, color=INDIGO, bg=INDIGO_LIGHT, size=36, icon_size=17, radius=11),
                    ft.Text("AI 阅卷中", size=18, weight=ft.FontWeight.W_700, color=INK),
                ],
                spacing=10,
            ),
            content=ft.Container(
                width=self.app._dialog_width(430),
                content=ft.Column(
                    [
                        status,
                        bar,
                        ft.Text(
                            "写作与翻译由 AI 按 15 分制评分并折算；客观题即时计分。",
                            size=10,
                            color=FAINT,
                        ),
                    ],
                    spacing=12,
                ),
            ),
        )
        self.app.page.show_dialog(dialog)

        def progress(message: str, value: float) -> None:
            status.value = message
            bar.value = max(0, min(1, value))
            try:
                self.app.page.update()
            except Exception:
                pass

        text = self.session.get("text_answers", {}) or {}
        writing_prompt = self.paper.get("writing", {}).get("prompt", "")
        translation_prompt = self.paper.get("translation", {}).get("prompt", "")
        ai_error = ""
        if (
            not self.app.ai.available
            and (
                (text.get("writing") or "").strip()
                or (text.get("translation") or "").strip()
            )
        ):
            ai_error = "AI 尚未配置，写作/翻译暂按 0 分记录；可在 AI 设置中配置后重新考试。 "
        writing_result: dict[str, Any] | None = None
        translation_result: dict[str, Any] | None = None
        try:
            progress("客观题计分…", 0.25)
            tasks = []
            if (text.get("writing") or "").strip() and self.app.ai.available:
                tasks.append(
                    self.app.ai.score_writing(
                        prompt=writing_prompt,
                        answer=text.get("writing", ""),
                        level=self.session.get("level", "CET-4"),
                        word_limit=tuple(self.paper.get("writing", {}).get("word_limit", [120, 180])),
                    )
                )
            else:
                tasks.append(self._none_result())
            if (text.get("translation") or "").strip() and self.app.ai.available:
                tasks.append(
                    self.app.ai.score_translation(
                        prompt=translation_prompt,
                        answer=text.get("translation", ""),
                        reference=self.paper.get("translation", {}).get("reference_answer", ""),
                        level=self.session.get("level", "CET-4"),
                    )
                )
            else:
                tasks.append(self._none_result())
            progress("AI 正在评分写作与翻译…", 0.55)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            if isinstance(results[0], Exception):
                ai_error += f"写作评分失败：{results[0]} "
            else:
                writing_result = results[0]
            if isinstance(results[1], Exception):
                ai_error += f"翻译评分失败：{results[1]} "
            else:
                translation_result = results[1]
            if writing_result is None:
                writing_result = {
                    "kind": "writing", "score_15": 0, "score_106": 0,
                    "feedback": "未填写作文或 AI 评分失败。", "strengths": [], "improvements": [],
                    "corrected_excerpt": "",
                }
            if translation_result is None:
                translation_result = {
                    "kind": "translation", "score_15": 0, "score_106": 0,
                    "feedback": "未填写译文或 AI 评分失败。", "strengths": [], "improvements": [],
                    "corrected_excerpt": "",
                }
            progress("保存成绩与错题…", 0.9)
            record = finalize_paper_exam(
                self.store,
                self.paper,
                self.session,
                writing_result=writing_result,
                translation_result=translation_result,
                completed_by=completed_by,
            )
            if ai_error:
                record["ai_scoring_error"] = ai_error.strip()
            self.session = None
            self.app.last_result = record
            try:
                self.app.page.pop_dialog()
            except Exception:
                pass
            if self.audio is not None:
                try:
                    await self.audio.pause()
                    await self.audio.release()
                except Exception:
                    pass
            self.app.navigate("result", record=record)
            if completed_by == "timeout":
                self.app.notify("考试时间到，系统已自动交卷。", "warning")
            else:
                self.app.notify("交卷成功，AI 评分完成。", "success")
        except Exception as exc:
            traceback.print_exc()
            try:
                self.app.page.pop_dialog()
            except Exception:
                pass
            self._submitting = False
            self._alive = True
            self.app.notify(f"交卷失败：{exc}。答题记录仍保存在本地。", "error")

    # ------------------------------------------------------------------- exit
    def _confirm_exit(self) -> None:
        def leave() -> None:
            self._save(touch_ui=False)
            self._alive = False
            self.app.navigate("home")
            self.app.notify("进度已保存。考试计时不会暂停。", "warning")

        self.app.confirm(
            "退出考试？",
            "答题与写作内容已自动保存，但考试计时不会暂停。可以从首页继续本次考试。",
            confirm_label="保存并退出",
            cancel_label="继续答题",
            on_confirm=leave,
        )

    def on_window_resize(self, width: float) -> None:
        if not self.active or self._submitting:
            return
        compact = width < 900
        if compact == self._layout_compact:
            return
        self._layout_compact = compact
        try:
            self.app.render()
        except Exception:
            pass

    # --------------------------------------------------------------- lifecycle
    def on_leave(self) -> None:
        if self.session and not self._submitting:
            self._save(touch_ui=False)
        if self.audio is not None and self._audio_started:
            self._pause_audio()
            self._audio_started = False
        self._alive = False

    def on_app_close(self) -> None:
        if self.session and not self._submitting:
            self._save(touch_ui=False)
        self._alive = False

