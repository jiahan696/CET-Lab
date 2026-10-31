from __future__ import annotations

from typing import TYPE_CHECKING

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
    empty_state,
    eyebrow,
    frosted_panel,
    glass_card,
    heading,
    icon_box,
    pill,
    progress_track,
    text_action,
)
from ..utils import fmt_duration, fmt_score, full_date, percent, short_date

if TYPE_CHECKING:
    from ..app import CETApp


class HistoryView:
    full_screen = False

    def __init__(self, app: "CETApp") -> None:
        self.app = app
        self.store = app.store
        self.records = app.store.history()

    def build(self) -> ft.Control:
        stats = self.store.stats()
        header = ft.Row(
            [
                ft.Column(
                    [
                        eyebrow("SCORE ARCHIVE · 成绩档案"),
                        heading("历史成绩", size=27),
                        body("每次模考自动归档。看分数，也看趋势。", size=12.5),
                    ],
                    spacing=2,
                    expand=True,
                ),
                pill(
                    f"最高 {fmt_score(stats['best_score'])} 分" if self.records else "尚无记录",
                    icon=ft.Icons.EMOJI_EVENTS_ROUNDED,
                    bg=SAND,
                    fg=WARNING,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        if not self.records:
            return ft.Column(
                [
                    header,
                    glass_card(
                        empty_state(
                            "还没有成绩记录",
                            "完成一次全真模考，成绩、单项分数与正确率会自动保存。",
                            icon=ft.Icons.INSIGHTS_ROUNDED,
                            action=action_button(
                                "开始全真模考",
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                on_click=lambda: self.app.navigate("exam"),
                            ),
                        ),
                        padding=16,
                    ),
                ],
                spacing=16,
            )
        return ft.Column(
            [
                header,
                self._stats_row(stats),
                ft.ResponsiveRow(
                    [self._trend_card(), self._overview_card(stats)],
                    spacing=16,
                    run_spacing=16,
                ),
                self._section_title(),
                ft.Column([self._record_card(r) for r in self.records], spacing=12),
            ],
            spacing=16,
        )

    def _stats_row(self, stats: dict) -> ft.Control:
        cells = [
            self._stat(ft.Icons.FACT_CHECK_ROUNDED, INDIGO, INDIGO_LIGHT, "完成模考", str(stats["exam_count"]), "次"),
            self._stat(ft.Icons.EMOJI_EVENTS_ROUNDED, WARNING, SAND, "最高总分", fmt_score(stats["best_score"]), "分"),
            self._stat(ft.Icons.INSIGHTS_ROUNDED, SUCCESS, MINT, "平均正确率", percent(stats["avg_accuracy"], 1), ""),
            self._stat(ft.Icons.TIMER_ROUNDED, DANGER, BLUSH, "最近总分", fmt_score(stats["last_score"]) if self.records else "—", "分"),
        ]
        return ft.ResponsiveRow(cells, spacing=14, run_spacing=14)

    def _stat(
        self,
        icon: ft.IconData,
        color: str,
        tint: str,
        label: str,
        value: str,
        suffix: str,
    ) -> ft.Control:
        return glass_card(
            ft.Row(
                [
                    icon_box(icon, color=color, bg=tint, size=38, icon_size=18, radius=12),
                    ft.Column(
                        [
                            ft.Text(label, size=10.5, color=FAINT, no_wrap=True),
                            ft.Row(
                                [
                                    ft.Text(value, size=22, weight=ft.FontWeight.W_700, color=INK, no_wrap=True),
                                    ft.Text(suffix, size=9.5, color=FAINT) if suffix else ft.Container(),
                                ],
                                spacing=2,
                                vertical_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                        spacing=1,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=16,
            col={"xs": 6, "md": 3},
        )

    # ------------------------------------------------------------------ trend
    def _trend_card(self) -> ft.Control:
        recent = list(reversed(self.records[:10]))
        bars = [self._bar(r, i == len(recent) - 1) for i, r in enumerate(recent)]
        chart = ft.Row(
            bars,
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.END,
            scroll=ft.ScrollMode.AUTO,
        )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("分数趋势", size=17, weight=ft.FontWeight.W_700, color=INK),
                                    body("最近 10 次模考总分 · 满分 710", size=11),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            pill("LAST 10", bg=TEAL_LIGHT, fg=TEAL_DARK, size=9),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=chart,
                        padding=ft.Padding.only(top=12),
                        height=205,
                    ),
                ],
                spacing=10,
            ),
            padding=22,
            col={"xs": 12, "lg": 7},
        )

    def _bar(self, record: dict, latest: bool) -> ft.Control:
        score = float(record.get("score", 0) or 0)
        height = max(14.0, min(126.0, 126.0 * score / 710.0))
        color = TEAL if latest else INDIGO
        bar = ft.Container(
            width=38,
            height=height,
            border_radius=ft.BorderRadius.only(top_left=9, top_right=9),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=[color, ft.Colors.with_opacity(0.48, color)],
            ),
            tooltip=f"{full_date(record.get('completed_at', ''))} · {fmt_score(score)} 分",
        )
        return ft.Column(
            [
                ft.Text(
                    fmt_score(score),
                    size=10,
                    color=color,
                    weight=ft.FontWeight.W_700,
                    no_wrap=True,
                ),
                ft.Container(
                    height=132,
                    alignment=ft.Alignment(0, 1),
                    content=bar,
                ),
                ft.Text(short_date(record.get("completed_at", "")), size=9, color=FAINT, no_wrap=True),
                ft.Container(width=4, height=4, border_radius=2, bgcolor=color if latest else "#E2E9F1"),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _overview_card(self, stats: dict) -> ft.Control:
        last = self.records[0]
        sections = last.get("sections", {})
        rows = []
        section_meta = [
            ("听力", "listening", TEAL, TEAL_LIGHT, ft.Icons.HEADPHONES_ROUNDED),
            ("阅读", "reading", INDIGO, INDIGO_LIGHT, ft.Icons.MENU_BOOK_ROUNDED),
            ("翻译", "translation", WARNING, SAND, ft.Icons.TRANSLATE_ROUNDED),
        ]
        if "writing" in sections:
            section_meta.insert(0, ("写作", "writing", SUCCESS, MINT, ft.Icons.EDIT_NOTE_ROUNDED))
        for label, key, color, tint, icon in section_meta:
            rows.append(
                ft.Row(
                    [
                        icon_box(icon, color=color, bg=tint, size=30, icon_size=14, radius=9),
                        ft.Text(label, size=11, color=INK_SOFT, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.Text(
                            fmt_score(sections.get(key, 0)),
                            size=13,
                            weight=ft.FontWeight.W_700,
                            color=INK,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("最近一次", size=17, weight=ft.FontWeight.W_700, color=INK),
                                    body(full_date(last.get("completed_at", "")), size=10.5),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            action_button(
                                "查看详情",
                                variant="secondary",
                                height=34,
                                font_size=11,
                                on_click=lambda: self.app.show_history_detail(last),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(fmt_score(last.get("score", 0)), size=34, weight=ft.FontWeight.W_800, color=TEAL_DARK),
                                        ft.Text("最近总分", size=9.5, color=FAINT),
                                    ],
                                    spacing=0,
                                ),
                                ft.Container(expand=True),
                                ft.Column(
                                    [
                                        ft.Text(percent(last.get("accuracy", 0)), size=16, weight=ft.FontWeight.W_700, color=INK),
                                        ft.Text("整体正确率", size=9.5, color=FAINT),
                                    ],
                                    spacing=0,
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                ),
                            ]
                        ),
                        padding=13,
                        border_radius=13,
                        bgcolor=ft.Colors.with_opacity(0.42, WHITE),
                        border=ft.Border.all(1, LINE_SOFT),
                    ),
                    ft.Column(rows, spacing=9),
                    divider(),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, size=14, color=WARNING),
                            ft.Text(
                                self._suggestion(last),
                                size=10.5,
                                color=INK_SOFT,
                                style=ft.TextStyle(height=1.5),
                                expand=True,
                            ),
                        ],
                        spacing=7,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                spacing=12,
            ),
            padding=22,
            col={"xs": 12, "lg": 5},
        )

    def _suggestion(self, record: dict) -> str:
        sections = record.get("sections", {}) or {}
        counts = record.get("section_counts", {}) or {}
        best_key = None
        lowest_ratio = 2.0
        for key in ("listening", "reading"):
            count = max(1, int(counts.get(key, 1) or 1))
            ratio = float((record.get("section_correct", {}) or {}).get(key, 0)) / count
            if ratio < lowest_ratio:
                lowest_ratio = ratio
                best_key = key
        label = {"listening": "听力", "reading": "阅读", "translation": "翻译"}.get(best_key, "阅读")
        return f"下一次优先补强「{label}」：先做专项题，再回来看解析里的同义替换与搭配。"

    def _section_title(self) -> ft.Control:
        return ft.Row(
            [
                ft.Text("全部记录", size=19, weight=ft.FontWeight.W_700, color=INK),
                ft.Container(expand=True),
                ft.Text(f"共 {len(self.records)} 次", size=10.5, color=FAINT, no_wrap=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _record_card(self, record: dict) -> ft.Control:
        sections = record.get("sections", {}) or {}
        timeout = record.get("completed_by") == "timeout"
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=42,
                                height=42,
                                border_radius=13,
                                bgcolor=SKY,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    [
                                        ft.Text(short_date(record.get("completed_at", "")), size=9.5, color=INDIGO),
                                        ft.Text(record.get("level", "CET-4").replace("CET-", ""), size=13, weight=ft.FontWeight.W_700, color=INK),
                                    ],
                                    spacing=0,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                record.get("paper_title") or (record.get("level", "CET-4") + " 全真模考"),
                                                size=14,
                                                weight=ft.FontWeight.W_700,
                                                color=INK,
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                            pill("自动交卷" if timeout else "手动交卷", bg=WARNING_BG if timeout else "#EEF5F2", fg=WARNING if timeout else SUCCESS, size=9),
                                        ],
                                        spacing=7,
                                    ),
                                    ft.Text(full_date(record.get("completed_at", "")), size=10, color=FAINT),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                [
                                    ft.Text(fmt_score(record.get("score", 0)), size=28, weight=ft.FontWeight.W_800, color=TEAL_DARK, no_wrap=True),
                                    ft.Text(f"/ 710", size=9, color=FAINT, no_wrap=True),
                                ],
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    divider(),
                    ft.Row(
                        (
                            [
                                self._section_cell("写作", sections.get("writing", 0), 106.5, SUCCESS),
                                self._section_cell("听力", sections.get("listening", 0), 248.5, TEAL),
                                self._section_cell("阅读", sections.get("reading", 0), 248.5, INDIGO),
                                self._section_cell("翻译", sections.get("translation", 0), 106.5, WARNING),
                            ]
                            if "writing" in sections
                            else [
                                self._section_cell("听力", sections.get("listening", 0), 248.5, TEAL),
                                self._section_cell("阅读", sections.get("reading", 0), 248.5, INDIGO),
                                self._section_cell("翻译", sections.get("translation", 0), 213, WARNING),
                                ft.Container(
                                    width=96,
                                    content=ft.Column(
                                        [
                                            ft.Text(percent(record.get("accuracy", 0)), size=16, weight=ft.FontWeight.W_700, color=INK, no_wrap=True),
                                            ft.Text("正确率", size=9.5, color=FAINT, no_wrap=True),
                                        ],
                                        spacing=0,
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                    ),
                                ),
                            ]
                        ),
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.SCHEDULE_ROUNDED, size=13, color=FAINT),
                            ft.Text(f"用时 {fmt_duration(record.get('duration_sec', 0))}", size=10, color=FAINT),
                            ft.Text(
                                f" · 客观题正确率 {percent(record.get('accuracy', 0))}" if "writing" in sections else "",
                                size=10,
                                color=FAINT,
                            ),
                            ft.Container(expand=True),
                            text_action(
                                "查看成绩详情",
                                lambda r=record: self.app.show_history_detail(r),
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                size=10.5,
                            ),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=11,
            ),
            padding=17,
        )

    def _section_cell(self, label: str, value, maximum: float, color: str) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, size=9.5, color=FAINT),
                    ft.Text(fmt_score(value), size=14, weight=ft.FontWeight.W_700, color=color, no_wrap=True),
                    progress_track(float(value) / maximum if maximum else 0, height=3, color=color),
                ],
                spacing=4,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            bgcolor=ft.Colors.with_opacity(0.38, WHITE),
            border=ft.Border.all(1, LINE_SOFT),
            border_radius=10,
            expand=True,
        )
