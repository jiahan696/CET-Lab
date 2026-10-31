from __future__ import annotations

import asyncio
import time
import traceback
from datetime import datetime
from typing import TYPE_CHECKING

import flet as ft

from ..exam_service import finalize_exam
from ..questions import section_cn, section_name
from ..scoring import (
    EXAM_DURATIONS,
    create_session,
    remaining_seconds,
    session_elapsed,
)
from ..theme import (
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
    SKY,
    SUCCESS,
    SUCCESS_BG,
    TEAL,
    TEAL_DARK,
    TEAL_LIGHT,
    WARNING,
    WHITE,
    action_button,
    body,
    divider,
    eyebrow,
    frosted_panel,
    glass_card,
    heading,
    icon_box,
    pill,
    progress_track,
    text_action,
)
from ..utils import fmt_clock, now_iso
from .qcomponents import (
    answer_text,
    material_block,
    option_item,
    question_meta_line,
    question_prompt,
)

if TYPE_CHECKING:
    from ..app import CETApp


class ExamView:
    def __init__(self, app: "CETApp") -> None:
        self.app = app
        self.store = app.store
        self.all_questions = app.questions
        self.session = self.store.active_exam
        self.full_screen = bool(self.session)
        self.selected_level = (
            self.session.get("level", "CET-4") if self.session else "CET-4"
        )
        self.exam_questions = self._session_questions()
        self.index = min(
            max(0, int(self.session.get("current", 0) or 0)),
            max(0, len(self.exam_questions) - 1),
        ) if self.session else 0
        self._alive = bool(self.session)
        self._timer_started = False
        self._submitting = False
        self._expired_on_open = bool(
            self.session and remaining_seconds(self.session) <= 0
        )
        self._timer_text: ft.Text | None = None
        self._timer_chip: ft.Container | None = None
        self._saved_label: ft.Text | None = None
        self._progress: ft.ProgressBar | None = None
        self._question_host: ft.Container | None = None
        self._sidebar_host: ft.Container | None = None

    # ------------------------------------------------------------------ data
    def _session_questions(self) -> list[dict]:
        if not self.session:
            return list(self.all_questions)
        ids = self.session.get("question_ids", [])
        by_id = {q["id"]: q for q in self.all_questions}
        questions = [by_id[qid] for qid in ids if qid in by_id]
        return questions or list(self.all_questions)

    @property
    def current_q(self) -> dict:
        return self.exam_questions[self.index]

    @property
    def answers(self) -> dict[str, list[str]]:
        if not self.session:
            return {}
        answers = self.session.setdefault("answers", {})
        return answers

    def current_answer(self) -> list[str]:
        return list(self.answers.get(self.current_q["id"], []) or [])

    # ----------------------------------------------------------------- build
    def build(self) -> ft.Control:
        if self.session:
            self.full_screen = True
            if self._expired_on_open:
                self._alive = False
                self.page_task_expire()
                return self._expired_screen()
            control = self._active_screen()
            if not self._timer_started:
                self._timer_started = True
                self.app.page.run_task(self._timer_loop)
            return control
        self.full_screen = False
        return self._intro_screen()

    def page_task_expire(self) -> None:
        self.app.page.run_task(self._expire_async)

    async def _expire_async(self) -> None:
        await asyncio.sleep(0.15)
        self._finalize("timeout")

    def _expired_screen(self) -> ft.Control:
        return ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            content=glass_card(
                ft.Column(
                    [
                        ft.ProgressRing(width=36, height=36, stroke_width=3, color=TEAL),
                        heading("考试时间已到", 22),
                        body("正在为你自动交卷并生成成绩…", 13),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=30,
                width=360,
            ),
        )

    # ----------------------------------------------------------------- intro
    def _intro_screen(self) -> ft.Control:
        back = self._round_icon(ft.Icons.ARROW_BACK_ROUNDED, lambda: self.app.navigate("home"))
        top = ft.Row(
            [
                back,
                ft.Column(
                    [
                        eyebrow("EXAM CENTER · 全真考场"),
                        ft.Text("全真模拟考试", size=24, weight=ft.FontWeight.W_700, color=INK),
                    ],
                    spacing=0,
                    expand=True,
                ),
                pill("45 题 · 710 分", bg=TEAL_LIGHT, fg=TEAL_DARK),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        main = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            pill("FULL MOCK", icon=ft.Icons.TIMER_ROUNDED, bg=INDIGO_LIGHT, fg=INDIGO),
                            pill("本地自动保存", icon=ft.Icons.SAVE_ROUNDED, bg="#EDF5F1", fg=SUCCESS, size=10),
                        ],
                        spacing=8,
                    ),
                    ft.Column(
                        [
                            heading("一次完整地，\n走完四六级考场。", size=34),
                            body(
                                "严格计时、答题卡导航、标记题目、交卷即出分。"
                                "所有作答实时写入本地 JSON，关闭程序后重新打开仍可继续。",
                                size=13,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            self._fact("45", "道题目", "听力 15 · 阅读 20 · 翻译 10"),
                            self._fact("710", "满分", "听力 / 阅读 / 翻译加权"),
                            self._fact("125/130", "分钟", "四级 / 六级标准时长"),
                        ],
                        spacing=10,
                    ),
                    ft.Column(
                        [
                            ft.Text("选择考试级别", size=11.5, color=FAINT, weight=ft.FontWeight.W_600),
                            ft.Row(
                                [
                                    self._level_card("CET-4", "四级 · 125 分钟", "基础 → 进阶"),
                                    self._level_card("CET-6", "六级 · 130 分钟", "进阶 → 挑战"),
                                ],
                                spacing=10,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            action_button(
                                f"开始 {self.selected_level} 全真模考",
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                height=50,
                                font_size=14,
                                on_click=self._begin_exam,
                            ),
                            action_button(
                                "返回首页",
                                variant="secondary",
                                height=50,
                                font_size=13,
                                on_click=lambda: self.app.navigate("home"),
                            ),
                        ],
                        spacing=10,
                        wrap=True,
                        run_spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=14, color=FAINT),
                            ft.Text(
                                "点击开始后计时立即生效；超时将自动强制交卷。",
                                size=10.5,
                                color=FAINT,
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=18,
            ),
            padding=28,
            col={"xs": 12, "lg": 8},
        )
        rules = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.SHIELD_ROUNDED, color=INDIGO, bg=INDIGO_LIGHT, size=38, icon_size=18, radius=12),
                            ft.Column(
                                [
                                    ft.Text("考场规则", size=16, weight=ft.FontWeight.W_700, color=INK),
                                    body("真实机考布局", size=11),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=10,
                    ),
                    divider(),
                    self._rule("01", "总倒计时置顶", "四级 125 分钟 / 六级 130 分钟，到点自动交卷。"),
                    self._rule("02", "右侧答题卡", "已答、未答、标记三种状态一眼可见，点题号直接跳转。"),
                    self._rule("03", "实时自动保存", "每次选择、跳题与标记都会写入本地 JSON。"),
                    self._rule("04", "交卷即出分", "输出总分、听力、阅读、翻译与整体正确率。"),
                    frosted_panel(
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, size=16, color=WARNING),
                                ft.Text(
                                    "建议先按真实考试节奏完成一次，再回到专项刷题补弱项。",
                                    size=11,
                                    color=INK_SOFT,
                                    style=ft.TextStyle(height=1.5),
                                    expand=True,
                                ),
                            ],
                            spacing=7,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        padding=12,
                        fill=0.45,
                    ),
                ],
                spacing=13,
            ),
            padding=22,
            col={"xs": 12, "lg": 4},
        )
        return ft.Column(
            [
                top,
                ft.ResponsiveRow([main, rules], spacing=16, run_spacing=16),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SHIELD_ROUNDED, size=13, color=FAINT),
                        ft.Text("无需联网 · 无后端 · 本机 JSON 存储", size=10.5, color=FAINT),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=16,
        )

    def _fact(self, value: str, label: str, detail: str) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(value, size=23, weight=ft.FontWeight.W_700, color=INK, no_wrap=True),
                    ft.Text(label, size=10.5, color=TEAL_DARK, weight=ft.FontWeight.W_600),
                    ft.Text(detail, size=9.5, color=FAINT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ],
                spacing=1,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            bgcolor=ft.Colors.with_opacity(0.46, WHITE),
            border=ft.Border.all(1, LINE_SOFT),
            border_radius=13,
            expand=True,
        )

    def _level_card(self, level: str, subtitle: str, note: str) -> ft.Container:
        selected = level == self.selected_level
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(level, size=18, weight=ft.FontWeight.W_800, color=TEAL_DARK if selected else INK),
                            ft.Container(expand=True),
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE_ROUNDED if selected else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                                size=17,
                                color=TEAL if selected else FAINT,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(subtitle, size=11, color=INK_SOFT if selected else MUTED),
                    ft.Text(note, size=9.5, color=FAINT),
                ],
                spacing=3,
            ),
            padding=14,
            bgcolor=ft.Colors.with_opacity(0.82, TEAL_LIGHT) if selected else ft.Colors.with_opacity(0.42, WHITE),
            border=ft.Border.all(1.4 if selected else 1, TEAL if selected else LINE),
            border_radius=16,
            expand=True,
            on_click=lambda _e, lv=level: self._select_level(lv),
            ink=True,
        )

    def _rule(self, number: str, title: str, detail: str) -> ft.Control:
        return ft.Row(
            [
                ft.Container(
                    width=26,
                    height=26,
                    border_radius=8,
                    bgcolor=TEAL_LIGHT,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(number, size=9.5, weight=ft.FontWeight.W_700, color=TEAL_DARK),
                ),
                ft.Column(
                    [
                        ft.Text(title, size=12, weight=ft.FontWeight.W_700, color=INK),
                        ft.Text(detail, size=10.5, color=MUTED, style=ft.TextStyle(height=1.45)),
                    ],
                    spacing=1,
                    expand=True,
                ),
            ],
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def _select_level(self, level: str) -> None:
        if self.session:
            return
        self.selected_level = level
        self.app.render()

    def _begin_exam(self) -> None:
        duration = EXAM_DURATIONS.get(self.selected_level, EXAM_DURATIONS["CET-4"])
        session = create_session(self.all_questions, self.selected_level, duration)
        self.session = session
        self.exam_questions = self._session_questions()
        self.index = 0
        self.store.set_active_exam(session)
        self.full_screen = True
        self._alive = True
        self._timer_started = False
        self._expired_on_open = False
        self.app.render()
        self.app.notify("考试已开始，计时进行中。", "info")

    # ---------------------------------------------------------------- active
    def _active_screen(self) -> ft.Control:
        header = self._header()
        self._question_host = ft.Container(content=self._question_content())
        self._sidebar_host = ft.Container(content=self._sidebar_content())
        question_card = glass_card(self._question_host, padding=22, col={"xs": 12, "lg": 9})
        sidebar_card = glass_card(self._sidebar_host, padding=18, col={"xs": 12, "lg": 3}, fill=0.62)
        body_column = ft.Column(
            [
                ft.ResponsiveRow(
                    [question_card, sidebar_card],
                    spacing=14,
                    run_spacing=14,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        return ft.Column(
            [
                ft.Container(content=header, padding=ft.Padding.only(left=18, right=18, top=12)),
                ft.Container(
                    content=body_column,
                    expand=True,
                    padding=ft.Padding.only(left=18, right=18, top=12, bottom=18),
                ),
            ],
            spacing=0,
            expand=True,
        )

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
                    ft.Icon(
                        ft.Icons.TIMER_ROUNDED,
                        size=15,
                        color=DANGER if remaining < 300 else TEAL,
                    ),
                    self._timer_text,
                ],
                spacing=6,
                tight=True,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            border_radius=12,
            bgcolor=DANGER_BG if remaining < 300 else TEAL_LIGHT,
            border=ft.Border.all(1, "#F0C9CF" if remaining < 300 else "#C9E3E0"),
        )
        answered_now = sum(1 for value in self.answers.values() if value)
        self._saved_label = ft.Text(
            f"{answered_now}/{len(self.exam_questions)} · 自动保存",
            size=9.5,
            color=FAINT,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._progress = progress_track(0, height=5, color=TEAL)
        title = ft.Column(
            [
                ft.Text(
                    f"{self.session.get('level', 'CET-4')} 模考",
                    size=15,
                    weight=ft.FontWeight.W_700,
                    color=INK,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                self._saved_label,
            ],
            spacing=1,
            expand=True,
        )
        top_row = ft.Row(
            [
                self._round_icon(ft.Icons.ARROW_BACK_ROUNDED, self._confirm_exit),
                title,
                self._timer_chip,
                action_button(
                    "交卷",
                    variant="primary",
                    height=36,
                    font_size=11.5,
                    on_click=self._confirm_submit,
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._refresh_header()
        return glass_card(
            ft.Column([top_row, self._progress], spacing=9),
            padding=ft.Padding.symmetric(horizontal=14, vertical=11),
            radius=20,
            fill=0.66,
        )

    def _round_icon(self, icon: ft.IconData, on_click) -> ft.Container:
        return ft.Container(
            width=34,
            height=34,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.55, WHITE),
            border=ft.Border.all(1, LINE_SOFT),
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(icon, size=17, color=INK_SOFT),
            on_click=lambda _e: on_click(),
            ink=True,
        )

    # --------------------------------------------------------------- question
    def _question_content(self) -> ft.Control:
        q = self.current_q
        answer = self.current_answer()
        number = self.index + 1
        total = len(self.exam_questions)
        options = ft.Column(
            [
                option_item(
                    chr(65 + i),
                    text,
                    selected=chr(65 + i) in answer,
                    on_click=self._choose,
                )
                for i, text in enumerate(q.get("options", []))
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        footer = self._question_footer()
        return ft.Column(
            [
                question_meta_line(q, number, total, marked=q["id"] in self._marked()),
                divider(),
                material_block(q),
                question_prompt(q),
                ft.Text(
                    "多选题：可选择多个选项，答案全部选对才计分。"
                    if q.get("type") == "multiple"
                    else "请选择一个最符合题意的选项。",
                    size=10.5,
                    color=FAINT,
                ),
                options,
                divider(),
                footer,
            ],
            spacing=13,
        )

    def _question_footer(self) -> ft.Control:
        qid = self.current_q["id"]
        marked = qid in self._marked()
        mark = text_action(
            "取消标记" if marked else "标记本题",
            self._toggle_mark,
            icon=ft.Icons.BOOKMARK_ROUNDED if marked else ft.Icons.BOOKMARK_BORDER_ROUNDED,
            color=WARNING if marked else MUTED,
            size=12,
        )
        prev_button = (
            action_button(
                "上一题",
                icon=ft.Icons.NAVIGATE_BEFORE_ROUNDED,
                variant="secondary",
                height=39,
                font_size=12,
                on_click=lambda: self._jump(self.index - 1),
            )
            if self.index > 0
            else ft.Container()
        )
        if self.index < len(self.exam_questions) - 1:
            next_button = action_button(
                "下一题",
                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                variant="secondary",
                height=39,
                font_size=12,
                on_click=lambda: self._jump(self.index + 1),
            )
        else:
            next_button = action_button(
                "交卷",
                icon=ft.Icons.FACT_CHECK_ROUNDED,
                height=39,
                font_size=12,
                on_click=self._confirm_submit,
            )
        return ft.Row(
            [
                mark,
                ft.Container(expand=True),
                prev_button,
                next_button,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _marked(self) -> list[str]:
        if not self.session:
            return []
        marked = self.session.setdefault("marked", [])
        return marked

    def _choose(self, key: str) -> None:
        if not self.session or self._submitting:
            return
        qid = self.current_q["id"]
        current = self.current_answer()
        if self.current_q.get("type") == "multiple":
            if key in current:
                current.remove(key)
            else:
                current.append(key)
        else:
            current = [key]
        if current:
            self.answers[qid] = sorted(current)
        else:
            self.answers.pop(qid, None)
        self._save(update_header=True)
        self._refresh_question()
        self._refresh_sidebar()

    def _jump(self, index: int, *, from_nav: bool = False) -> None:
        if not self.session:
            return
        index = max(0, min(len(self.exam_questions) - 1, int(index)))
        self.index = index
        self.session["current"] = index
        self._save(update_header=False)
        self._refresh_question()
        self._refresh_sidebar()
        if from_nav:
            try:
                self.app.page.scroll_to(offset=0, duration=220)
            except Exception:
                pass

    def _toggle_mark(self) -> None:
        if not self.session:
            return
        qid = self.current_q["id"]
        marked = self._marked()
        if qid in marked:
            marked.remove(qid)
        else:
            marked.append(qid)
        self._save(update_header=False)
        self._refresh_question()
        self._refresh_sidebar()

    # ----------------------------------------------------------------- sidebar
    def _sidebar_content(self) -> ft.Control:
        answered = sum(1 for v in self.answers.values() if v)
        total = len(self.exam_questions)
        marked_count = len(self._marked())
        legend = ft.Row(
            [
                self._legend_dot(TEAL, "已答"),
                self._legend_dot("#DCE7EF", "未答"),
                self._legend_dot(WARNING, "标记"),
            ],
            spacing=10,
            tight=True,
        )
        nav_sections = self._nav_sections()
        mark_label = "取消标记" if self.current_q["id"] in self._marked() else "标记本题"
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("答题卡", size=16, weight=ft.FontWeight.W_700, color=INK),
                        ft.Container(expand=True),
                        pill(f"{answered}/{total}", bg=TEAL_LIGHT, fg=TEAL_DARK, size=10),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        legend,
                        ft.Container(expand=True),
                        ft.Text(f"{marked_count} 个标记", size=9.5, color=FAINT, no_wrap=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                divider(),
                nav_sections,
                divider(),
                ft.Row(
                    [
                        text_action(
                            mark_label,
                            self._toggle_mark,
                            icon=ft.Icons.BOOKMARK_ROUNDED if mark_label == "取消标记" else ft.Icons.BOOKMARK_BORDER_ROUNDED,
                            color=WARNING if mark_label == "取消标记" else MUTED,
                            size=11,
                        ),
                        ft.Container(expand=True),
                        ft.Text(f"第 {self.index + 1} 题", size=10, color=FAINT, no_wrap=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                action_button(
                    "提交试卷",
                    icon=ft.Icons.FACT_CHECK_ROUNDED,
                    height=40,
                    font_size=12.5,
                    on_click=self._confirm_submit,
                ),
                ft.Text(
                    "答题进度自动保存至本地",
                    size=9.5,
                    color=FAINT,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=11,
        )

    def _legend_dot(self, color: str, label: str) -> ft.Control:
        return ft.Row(
            [
                ft.Container(width=8, height=8, border_radius=3, bgcolor=color),
                ft.Text(label, size=9.5, color=MUTED, no_wrap=True),
            ],
            spacing=4,
            tight=True,
        )

    def _nav_sections(self) -> ft.Control:
        sections: list[ft.Control] = []
        current_id = self.current_q["id"]
        marked = set(self._marked())
        for category in ("listening", "reading", "translation"):
            group = [q for q in self.exam_questions if q.get("category") == category]
            if not group:
                continue
            buttons = []
            for q in group:
                num = self.exam_questions.index(q) + 1
                answered = bool(self.answers.get(q["id"]))
                is_current = q["id"] == current_id
                is_marked = q["id"] in marked
                if is_current:
                    bg = TEAL
                    fg = WHITE
                    border = ft.Border.all(1.5, TEAL_DARK)
                elif answered:
                    bg = "#D8ECE7"
                    fg = TEAL_DARK
                    border = ft.Border.all(1, "#B8DCD4")
                else:
                    bg = ft.Colors.with_opacity(0.46, WHITE)
                    fg = MUTED
                    border = ft.Border.all(1, LINE_SOFT)
                dot = (
                    ft.Container(
                        width=6,
                        height=6,
                        border_radius=3,
                        bgcolor=WARNING if not is_current else "#FFE2AE",
                        right=2,
                        top=2,
                    )
                    if is_marked
                    else ft.Container(width=0, height=0)
                )
                buttons.append(
                    ft.Container(
                        width=34,
                        height=31,
                        border_radius=9,
                        bgcolor=bg,
                        border=border,
                        on_click=lambda _e, idx=self.exam_questions.index(q): self._jump(idx, from_nav=True),
                        content=ft.Stack(
                            [
                                ft.Container(
                                    width=34,
                                    height=31,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text(
                                        str(num),
                                        size=10.5,
                                        color=fg,
                                        weight=ft.FontWeight.W_700 if (answered or is_current) else ft.FontWeight.W_500,
                                        no_wrap=True,
                                    ),
                                ),
                                dot,
                            ],
                            width=34,
                            height=31,
                        ),
                    )
                )
            sections.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    section_cn(category),
                                    size=10,
                                    weight=ft.FontWeight.W_700,
                                    color=INK_SOFT,
                                ),
                                ft.Container(expand=True),
                                ft.Text(f"{len(group)} 题", size=9, color=FAINT, no_wrap=True),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(buttons, spacing=6, run_spacing=6, wrap=True),
                    ],
                    spacing=6,
                )
            )
        return ft.Column(sections, spacing=11)

    # ------------------------------------------------------------------ timer
    async def _timer_loop(self) -> None:
        while self._alive and self.session and not self._submitting:
            remaining = remaining_seconds(self.session)
            if remaining <= 0:
                self._finalize("timeout")
                break
            if self._timer_text is not None:
                self._timer_text.value = fmt_clock(remaining)
                danger = remaining < 300
                self._timer_text.color = DANGER if danger else INK
                if self._timer_chip is not None:
                    self._timer_chip.bgcolor = DANGER_BG if danger else TEAL_LIGHT
                    self._timer_chip.border = ft.Border.all(
                        1, "#F0C9CF" if danger else "#C9E3E0"
                    )
                try:
                    self._timer_text.update()
                    if self._timer_chip is not None:
                        self._timer_chip.update()
                except Exception:
                    pass
            if int(remaining) % 12 == 0:
                self._save(update_header=False, touch_ui=False)
            await asyncio.sleep(1)

    # ------------------------------------------------------------------- save
    def _save(self, *, update_header: bool = False, touch_ui: bool = True) -> None:
        if not self.session:
            return
        self.session["current"] = self.index
        self.session["saved_at"] = now_iso()
        self.store.set_active_exam(self.session)
        if self._saved_label is not None:
            answered_now = sum(1 for value in self.answers.values() if value)
            self._saved_label.value = (
                f"{answered_now}/{len(self.exam_questions)} · "
                + datetime.now().strftime("%H:%M:%S")
            )
        if update_header:
            self._refresh_header()
        if touch_ui:
            try:
                self.app.page.update()
            except Exception:
                pass

    def _refresh_header(self) -> None:
        if not self.session:
            return
        answered = sum(1 for v in self.answers.values() if v)
        total = len(self.exam_questions)
        if self._progress is not None:
            self._progress.value = answered / max(1, total)

    def _refresh_question(self) -> None:
        if self._question_host is not None:
            self._question_host.content = self._question_content()
        self._refresh_header()
        try:
            self.app.page.update()
        except Exception:
            pass

    def _refresh_sidebar(self) -> None:
        if self._sidebar_host is not None:
            self._sidebar_host.content = self._sidebar_content()
        try:
            self.app.page.update()
        except Exception:
            pass

    # ------------------------------------------------------------------ exit
    def _confirm_exit(self) -> None:
        def leave() -> None:
            self._save(update_header=False)
            self._alive = False
            self.app.navigate("home")
            self.app.notify("进度已保存。考试计时不会暂停。", "warning")

        self.app.confirm(
            "退出考试？",
            "答题进度已经实时保存，但考试计时不会暂停。你可以随时从首页继续本次考试。",
            confirm_label="保存并退出",
            cancel_label="继续答题",
            on_confirm=leave,
        )

    # ---------------------------------------------------------------- submit
    def _confirm_submit(self) -> None:
        if not self.session or self._submitting:
            return
        answered = sum(1 for v in self.answers.values() if v)
        total = len(self.exam_questions)
        unanswered = total - answered
        message = (
            f"你还有 {unanswered} 道题未作答。确认交卷后将立即阅卷并生成本次成绩，"
            "交卷后不可修改答案。"
            if unanswered
            else "所有题目均已作答。确认交卷后将立即阅卷并生成本次成绩。"
        )

        def submit() -> None:
            self._finalize("manual")

        self.app.confirm(
            "确认提交试卷？",
            message,
            confirm_label="确认交卷",
            cancel_label="继续答题",
            on_confirm=submit,
        )

    def _finalize(self, completed_by: str) -> None:
        if not self.session or self._submitting:
            return
        self._submitting = True
        self._alive = False
        try:
            record = finalize_exam(
                self.store,
                self.all_questions,
                self.session,
                completed_by=completed_by,
            )
            self.session = None
            self.app.last_result = record
            try:
                self.app.page.pop_dialog()
            except Exception:
                pass
            self.app.navigate("result", record=record)
            if completed_by == "timeout":
                self.app.notify("考试时间已到，系统已自动交卷。", "warning")
            else:
                self.app.notify("交卷成功，成绩已生成。", "success")
        except Exception:
            traceback.print_exc()
            self._submitting = False
            self._alive = True
            self.app.notify("交卷时遇到问题，答题记录仍保存在本地。", "error")

    # --------------------------------------------------------------- lifecycle
    def on_leave(self) -> None:
        if self.session and not self._submitting:
            self._save(update_header=False, touch_ui=False)
        self._alive = False

    def on_app_close(self) -> None:
        if self.session and not self._submitting:
            self._save(update_header=False, touch_ui=False)
        self._alive = False
