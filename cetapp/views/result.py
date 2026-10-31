from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

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
    eyebrow,
    frosted_panel,
    glass_card,
    heading,
    icon_box,
    pill,
    progress_track,
)
from ..utils import fmt_duration, fmt_score, full_date, percent

if TYPE_CHECKING:
    from ..app import CETApp


SECTION_META = (
    ("listening", "听力", 248.5, TEAL, TEAL_LIGHT, ft.Icons.HEADPHONES_ROUNDED, "Listening"),
    ("reading", "阅读", 248.5, INDIGO, INDIGO_LIGHT, ft.Icons.MENU_BOOK_ROUNDED, "Reading"),
    ("translation", "翻译", 213.0, WARNING, SAND, ft.Icons.TRANSLATE_ROUNDED, "Translation"),
)
PAPER_SECTION_META = (
    ("writing", "写作", 106.5, SUCCESS, MINT, ft.Icons.EDIT_NOTE_ROUNDED, "Writing"),
    ("listening", "听力", 248.5, TEAL, TEAL_LIGHT, ft.Icons.HEADPHONES_ROUNDED, "Listening"),
    ("reading", "阅读", 248.5, INDIGO, INDIGO_LIGHT, ft.Icons.MENU_BOOK_ROUNDED, "Reading"),
    ("translation", "翻译", 106.5, WARNING, SAND, ft.Icons.TRANSLATE_ROUNDED, "Translation"),
)


class ResultView:
    full_screen = False

    def __init__(self, app: "CETApp", record: dict[str, Any]) -> None:
        self.app = app
        self.store = app.store
        self.record = record

    def build(self) -> ft.Control:
        return ft.Column(
            [
                self._top(),
                self._hero(),
                self._section_cards(),
                self._ai_feedback(),
                self._lower(),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SHIELD_ROUNDED, size=13, color=FAINT),
                        ft.Text("成绩已写入本地历史记录", size=10.5, color=FAINT),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=16,
        )

    def _top(self) -> ft.Control:
        return ft.Row(
            [
                ft.Column(
                    [
                        eyebrow("SCORE REPORT · 成绩报告"),
                        ft.Text("本次模考成绩", size=25, weight=ft.FontWeight.W_700, color=INK),
                    ],
                    spacing=0,
                    expand=True,
                ),
                pill(
                    "自动交卷" if self.record.get("completed_by") == "timeout" else "手动交卷",
                    icon=ft.Icons.TIMER_ROUNDED if self.record.get("completed_by") == "timeout" else ft.Icons.CHECK_CIRCLE_ROUNDED,
                    bg=WARNING_BG if self.record.get("completed_by") == "timeout" else "#EDF5F1",
                    fg=WARNING if self.record.get("completed_by") == "timeout" else SUCCESS,
                    size=10,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _hero(self) -> ft.Control:
        score = float(self.record.get("score", 0) or 0)
        accuracy = float(self.record.get("accuracy", 0) or 0)
        passed = score >= 425
        color = TEAL if passed else WARNING
        ring = ft.ProgressRing(
            value=max(0.0, min(1.0, score / 710.0)),
            width=176,
            height=176,
            stroke_width=10,
            color=color,
            bgcolor="#E6EEF3",
        )
        gauge = ft.Stack(
            [
                ring,
                ft.Container(
                    width=176,
                    height=176,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        [
                            ft.Text("总分", size=10, color=FAINT),
                            ft.Text(fmt_score(score), size=45, weight=ft.FontWeight.W_800, color=INK, no_wrap=True),
                            ft.Text("/ 710", size=10, color=FAINT),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
            width=176,
            height=176,
        )
        info = ft.Column(
            [
                ft.Row(
                    [
                        pill(
                            "达到 425 分" if passed else "继续加油",
                            icon=ft.Icons.EMOJI_EVENTS_ROUNDED if passed else ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
                            bg=SUCCESS_BG if passed else WARNING_BG,
                            fg=SUCCESS if passed else WARNING,
                        ),
                        pill(self.record.get("level", "CET-4"), bg=SKY, fg=INK_SOFT),
                    ],
                    spacing=8,
                ),
                heading(
                    "这次，离 710 更近了。" if passed else "把错题变成下一次的分数。",
                    size=30,
                ),
                body(
                    "成绩已经归档。下面把听力、阅读、翻译拆开看，"
                    "再用错题本把失分点逐个补上。",
                    size=12.5,
                ),
                ft.Row(
                    [
                        self._mini_stat(
                            ft.Icons.FACT_CHECK_ROUNDED,
                            "客观题正确率" if "writing" in (self.record.get("sections", {}) or {}) else "正确率",
                            percent(accuracy),
                        ),
                        self._mini_stat(ft.Icons.SCHEDULE_ROUNDED, "用时", fmt_duration(self.record.get("duration_sec", 0))),
                        self._mini_stat(ft.Icons.CALENDAR_MONTH_ROUNDED, "交卷时间", full_date(self.record.get("completed_at", ""))),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                ft.Row(
                    [
                        action_button(
                            "查看错题本",
                            icon=ft.Icons.BOOKMARK_ROUNDED,
                            on_click=lambda: self.app.navigate("wrongbook"),
                        ),
                        action_button(
                            "再考一次",
                            icon=ft.Icons.REPLAY_ROUNDED,
                            variant="secondary",
                            on_click=lambda: self.app.navigate("exam"),
                        ),
                        action_button(
                            "返回首页",
                            variant="ghost",
                            icon=ft.Icons.HOME_ROUNDED,
                            on_click=lambda: self.app.navigate("home"),
                        ),
                    ],
                    spacing=9,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
            spacing=12,
            expand=True,
        )
        return glass_card(
            ft.ResponsiveRow(
                [
                    ft.Container(
                        content=gauge,
                        alignment=ft.Alignment(0, 0),
                        col={"xs": 12, "md": 4},
                    ),
                    ft.Container(content=info, col={"xs": 12, "md": 8}),
                ],
                spacing=18,
                run_spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=26,
            fill=0.68,
        )

    def _mini_stat(self, icon: ft.IconData, label: str, value: str) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=14, color=FAINT),
                    ft.Column(
                        [
                            ft.Text(label, size=9, color=FAINT, no_wrap=True),
                            ft.Text(
                                value,
                                size=11.5,
                                color=INK_SOFT,
                                weight=ft.FontWeight.W_600,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            bgcolor=ft.Colors.with_opacity(0.38, WHITE),
            border=ft.Border.all(1, LINE_SOFT),
            border_radius=10,
        )

    def _section_cards(self) -> ft.Control:
        sections = self.record.get("sections", {}) or {}
        counts = self.record.get("section_counts", {}) or {}
        correct = self.record.get("section_correct", {}) or {}
        meta = PAPER_SECTION_META if "writing" in sections else SECTION_META
        cards = []
        for key, label, maximum, color, tint, icon, en in meta:
            value = float(sections.get(key, 0) or 0)
            count = int(counts.get(key, 0) or 0)
            total = max(1, count)
            right = int(correct.get(key, 0) or 0)
            cards.append(
                glass_card(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    icon_box(icon, color=color, bg=tint, size=40, icon_size=19, radius=13),
                                    ft.Column(
                                        [
                                            ft.Text(label, size=14, weight=ft.FontWeight.W_700, color=INK),
                                            ft.Text(en.upper(), size=8.5, color=FAINT),
                                        ],
                                        spacing=0,
                                    ),
                                    ft.Container(expand=True),
                                    ft.Text(fmt_score(value), size=25, weight=ft.FontWeight.W_800, color=color, no_wrap=True),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            progress_track(value / maximum if maximum else 0, height=7, color=color),
                            ft.Row(
                                [
                                    ft.Text(f"满分 {fmt_score(maximum)}", size=9.5, color=FAINT),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        (
                                            f"AI {self.record.get(key, {}).get('score_15', 0)}/15"
                                            if key in ("writing", "translation")
                                            else ("本卷未提供" if count == 0 else f"{right}/{total} 题正确")
                                        ),
                                        size=9.5,
                                        color=INK_SOFT,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                ]
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=17,
                    col={"xs": 12, "sm": 6, "lg": 3} if "writing" in sections else {"xs": 12, "sm": 4},
                    fill=0.60,
                )
            )
        return ft.ResponsiveRow(cards, spacing=14, run_spacing=14)

    def _ai_feedback(self) -> ft.Control:
        writing = self.record.get("writing") or {}
        translation = self.record.get("translation") or {}
        if not writing and not translation:
            return ft.Container()
        cards = []
        for title, data, color, tint, icon in (
            ("AI 写作评分", writing, SUCCESS, MINT, ft.Icons.EDIT_NOTE_ROUNDED),
            ("AI 翻译评分", translation, WARNING, SAND, ft.Icons.TRANSLATE_ROUNDED),
        ):
            if not data:
                continue
            strengths = data.get("strengths") or []
            improvements = data.get("improvements") or []
            cards.append(
                glass_card(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    icon_box(icon, color=color, bg=tint, size=38, icon_size=18, radius=12),
                                    ft.Column(
                                        [
                                            ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=INK),
                                            ft.Text(
                                                f"{data.get('score_15', 0)} / 15 · 折算 {fmt_score(data.get('score_106', 0))} 分",
                                                size=9.5,
                                                color=FAINT,
                                            ),
                                        ],
                                        spacing=0,
                                        expand=True,
                                    ),
                                    pill("AI", bg=tint, fg=color, size=9),
                                ],
                                spacing=9,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                data.get("feedback", ""),
                                size=11.5,
                                color=INK_SOFT,
                                selectable=True,
                                style=ft.TextStyle(height=1.6),
                            ),
                            *(
                                [
                                    ft.Text(
                                        "提升建议：" + "；".join(improvements[:3]),
                                        size=10,
                                        color=MUTED,
                                        style=ft.TextStyle(height=1.5),
                                    )
                                ]
                                if improvements
                                else []
                            ),
                            *(
                                [
                                    frosted_panel(
                                        ft.Text(
                                            "修改示例：" + data.get("corrected_excerpt", ""),
                                            size=10,
                                            color=INK_SOFT,
                                            selectable=True,
                                            style=ft.TextStyle(height=1.55),
                                        ),
                                        padding=10,
                                        fill=0.36,
                                    )
                                ]
                                if data.get("corrected_excerpt")
                                else []
                            ),
                        ],
                        spacing=9,
                    ),
                    padding=17,
                    col={"xs": 12, "lg": 6},
                    fill=0.58,
                )
            )
        error = self.record.get("ai_scoring_error")
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("AI 评分详情", size=17, weight=ft.FontWeight.W_700, color=INK),
                        ft.Container(expand=True),
                        pill("15 分制折算", bg=INDIGO_LIGHT, fg=INDIGO, size=9),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                *(
                    [
                        ft.Container(
                            content=ft.Text(f"评分提示：{error}", size=10, color=DANGER),
                            padding=10,
                            border_radius=10,
                            bgcolor=DANGER_BG,
                        )
                    ]
                    if error
                    else []
                ),
                ft.ResponsiveRow(cards, spacing=14, run_spacing=14),
            ],
            spacing=10,
        )

    def _lower(self) -> ft.Control:
        correct = int(self.record.get("correct", 0) or 0)
        total = int(self.record.get("total", 45) or 45)
        unanswered = int(self.record.get("unanswered", 0) or 0)
        wrong = max(0, total - correct - unanswered)
        stats = [
            ("答对", str(correct), SUCCESS, MINT),
            ("答错", str(wrong), DANGER, BLUSH),
            ("未答", str(unanswered), WARNING, SAND),
            (
                "客观题正确率" if "writing" in (self.record.get("sections", {}) or {}) else "正确率",
                percent(self.record.get("accuracy", 0)),
                TEAL,
                TEAL_LIGHT,
            ),
        ]
        cells = []
        for label, value, color, tint in stats:
            cells.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(value, size=21, weight=ft.FontWeight.W_700, color=color, no_wrap=True),
                            ft.Text(label, size=9.5, color=FAINT, no_wrap=True),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=11),
                    bgcolor=ft.Colors.with_opacity(0.38, WHITE),
                    border=ft.Border.all(1, LINE_SOFT),
                    border_radius=12,
                    expand=True,
                )
            )
        breakdown = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("答题概况", size=16, weight=ft.FontWeight.W_700, color=INK),
                            ft.Container(expand=True),
                            pill(f"错题 {wrong} 道", bg=BLUSH, fg=DANGER, size=9.5),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(cells, spacing=8),
                    divider(),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.BOOKMARK_ROUNDED, size=15, color=DANGER),
                            ft.Text(
                                f"{wrong} 道错误作答已自动收录错题本，可随时重做。",
                                size=10.5,
                                color=INK_SOFT,
                                expand=True,
                            ),
                            action_button(
                                "去复盘",
                                variant="secondary",
                                height=33,
                                font_size=10.5,
                                on_click=lambda: self.app.navigate("wrongbook"),
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=12,
            ),
            padding=20,
            col={"xs": 12, "lg": 7},
        )
        next_step = self._next_step()
        return ft.ResponsiveRow([breakdown, next_step], spacing=16, run_spacing=16)

    def _next_step(self) -> ft.Control:
        sections = self.record.get("sections", {}) or {}
        counts = self.record.get("section_counts", {}) or {}
        correct = self.record.get("section_correct", {}) or {}
        weak_key = "reading"
        weakest = 2.0
        for key in ("listening", "reading"):
            total = max(1, int(counts.get(key, 1) or 1))
            ratio = int(correct.get(key, 0) or 0) / total
            if ratio < weakest:
                weakest = ratio
                weak_key = key
        meta = next((m for m in SECTION_META if m[0] == weak_key), SECTION_META[1])
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("下一步建议", size=16, weight=ft.FontWeight.W_700, color=INK),
                                    body("把失分点变成可执行任务", size=10.5),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            pill("NEXT", bg=INDIGO_LIGHT, fg=INDIGO, size=9),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    frosted_panel(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        icon_box(meta[5], color=meta[3], bg=meta[4], size=36, icon_size=17, radius=11),
                                        ft.Column(
                                            [
                                                ft.Text(f"优先补强 · {meta[1]}", size=12.5, weight=ft.FontWeight.W_700, color=INK),
                                                ft.Text(
                                                    f"本次正确率 {weakest * 100:.0f}%",
                                                    size=10,
                                                    color=FAINT,
                                                ),
                                            ],
                                            spacing=0,
                                        ),
                                    ],
                                    spacing=9,
                                ),
                                ft.Text(
                                    "先去专项刷题做 5 道同类题，再回错题本重做本次失分题；"
                                    "下一套模考重点观察这一项的分数变化。",
                                    size=11,
                                    color=INK_SOFT,
                                    style=ft.TextStyle(height=1.55),
                                ),
                                action_button(
                                    "去专项刷题",
                                    icon=ft.Icons.EDIT_NOTE_ROUNDED,
                                    variant="secondary",
                                    height=38,
                                    font_size=11.5,
                                    on_click=lambda: self.app.navigate("practice"),
                                ),
                            ],
                            spacing=9,
                        ),
                        padding=13,
                        fill=0.46,
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=14, color=INDIGO),
                            ft.Text(
                                "AI 学习计划接口已预留，可在设置中接入大模型。",
                                size=9.5,
                                color=FAINT,
                                expand=True,
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=11,
            ),
            padding=20,
            col={"xs": 12, "lg": 5},
            fill=0.64,
        )
