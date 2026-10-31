from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ..questions import CATEGORY_LABELS
from ..scoring import remaining_seconds
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
from ..utils import fmt_clock, fmt_score, full_date, percent, short_date

if TYPE_CHECKING:
    from ..app import CETApp


def _feature_card(
    icon: ft.IconData,
    title: str,
    description: str,
    accent: str,
    tint: str,
    on_click,
    tag: str | None = None,
) -> ft.Container:
    top_controls: list[ft.Control] = [icon_box(icon, color=accent, bg=tint, size=46)]
    top_controls.append(ft.Container(expand=True))
    if tag:
        top_controls.append(pill(tag, bg=tint, fg=accent, size=11))
    top_controls.append(ft.Icon(ft.Icons.ARROW_OUTWARD_ROUNDED, size=17, color=FAINT))
    return glass_card(
        ft.Column(
            [
                ft.Row(top_controls, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                ft.Column(
                    [
                        ft.Text(title, size=17, weight=ft.FontWeight.W_700, color=INK),
                        body(description, size=12.5, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    spacing=4,
                ),
            ],
            spacing=16,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=20,
        height=168,
        on_click=lambda _e: on_click(),
        ink=True,
        col={"xs": 12, "sm": 6, "lg": 3},
    )


def _stat_card(
    icon: ft.IconData,
    tint: str,
    accent: str,
    label: str,
    value: str,
    detail: str,
) -> ft.Container:
    return glass_card(
        ft.Column(
            [
                ft.Row(
                    [
                        icon_box(icon, color=accent, bg=tint, size=38, icon_size=18, radius=12),
                        ft.Container(expand=True),
                        ft.Text(detail, size=10.5, color=FAINT, no_wrap=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(value, size=27, weight=ft.FontWeight.W_700, color=INK, no_wrap=True),
                        ft.Text(label, size=12, color=MUTED, no_wrap=True),
                    ],
                    spacing=1,
                ),
            ],
            spacing=14,
        ),
        padding=18,
        col={"xs": 6, "sm": 6, "md": 3},
    )


class DashboardView:
    def __init__(self, app: "CETApp") -> None:
        self.app = app
        self.store = app.store
        self.stats = app.store.stats()

    def build(self) -> ft.Control:
        return ft.Column(
            [
                self._hero(),
                self._stats_row(),
                self._section_header("开始学习", "四条路径，覆盖输入、输出与复盘"),
                self._features(),
                self._lower_grid(),
                self._footer(),
            ],
            spacing=18,
        )

    # ------------------------------------------------------------------ hero
    def _hero(self) -> ft.Control:
        active = self.store.active_exam
        hero = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            pill("CET-4 / CET-6", icon=ft.Icons.SCHOOL_ROUNDED, bg=TEAL_LIGHT, fg=TEAL_DARK),
                            pill("内置题库 + 试卷导入", bg=INDIGO_LIGHT, fg=INDIGO),
                            pill("LOCAL ONLY", icon=ft.Icons.WIFI_OFF_ROUNDED, bg="#EFF4F1", fg=SUCCESS, size=10),
                        ],
                        spacing=8,
                        wrap=True,
                        run_spacing=8,
                    ),
                    ft.Column(
                        [
                            eyebrow("LIQUID GLASS EXAM STUDIO"),
                            heading("把每一次练习，\n都当成走进考场。", size=34),
                            body(
                                "全真计时、自动保存、AI 阅卷。内置 45 道专项题，也可导入完整真题："
                                "写作、听力音频、左文右题阅读、全文翻译，一套流程练到考场手感。",
                                size=13.5,
                                max_lines=3,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            action_button(
                                "开始全真模考",
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                on_click=lambda: self.app.navigate("exam"),
                            ),
                            action_button(
                                "专项刷题",
                                icon=ft.Icons.EDIT_NOTE_ROUNDED,
                                variant="secondary",
                                on_click=lambda: self.app.navigate("practice"),
                            ),
                        ],
                        spacing=10,
                        wrap=True,
                        run_spacing=10,
                    ),
                    ft.Row(
                        [
                            self._micro_info(ft.Icons.TIMER_ROUNDED, "125 / 130 分钟"),
                            self._micro_info(ft.Icons.SAVE_ROUNDED, "实时自动保存"),
                            self._micro_info(ft.Icons.FACT_CHECK_ROUNDED, "交卷即出分"),
                        ],
                        spacing=18,
                        wrap=True,
                        run_spacing=8,
                    ),
                ],
                spacing=20,
            ),
            padding=28,
            col={"xs": 12, "lg": 8},
        )
        return ft.ResponsiveRow(
            [hero, self._focus_panel(active)],
            spacing=16,
            run_spacing=16,
        )

    def _micro_info(self, icon: ft.IconData, text: str) -> ft.Control:
        return ft.Row(
            [
                ft.Icon(icon, size=14, color=FAINT),
                ft.Text(text, size=11, color=MUTED, no_wrap=True),
            ],
            spacing=5,
            tight=True,
        )

    def _focus_panel(self, active: dict | None) -> ft.Control:
        if active:
            paper = self.app.library.get(active.get("paper_id", "")) if active.get("paper_id") else None
            if paper:
                from ..paperlib import paper_questions
                total = len(paper_questions(paper))
                paper_title = paper.get("paper", {}).get("title", "")
            else:
                total = len(active.get("question_ids", []))
                paper_title = active.get("level", "CET-4")
            answered = len([v for v in (active.get("answers", {}) or {}).values() if v])
            remaining = remaining_seconds(active)
            inner = ft.Column(
                [
                    self._panel_header("未完成模考", "计时仍在继续"),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("剩余时间", size=11, color=FAINT),
                                ft.Text(
                                    fmt_clock(remaining),
                                    size=38,
                                    weight=ft.FontWeight.W_700,
                                    color=DANGER if remaining < 300 else INK,
                                    no_wrap=True,
                                ),
                                ft.Text(
                                    f"{paper_title or active.get('level', 'CET-4')} · 已答 {answered}/{total} 题",
                                    size=10.5,
                                    color=MUTED,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=2,
                        ),
                        padding=18,
                        border_radius=18,
                        bgcolor=ft.Colors.with_opacity(0.46, WHITE),
                        border=ft.Border.all(1, LINE_SOFT),
                    ),
                    progress_track(answered / max(1, total), color=TEAL),
                    action_button(
                        "继续上次考试",
                        icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                        on_click=lambda: self.app.navigate("exam"),
                        expand=True,
                    ),
                    body("答题卡与剩余时间已保存在本机，退出程序也不会丢失。", size=11.5),
                ],
                spacing=13,
            )
        else:
            history = self.store.history()
            last = history[0] if history else None
            previous = history[1] if len(history) > 1 else None
            score = float(last.get("score", 0)) if last else 0.0
            delta = score - float(previous.get("score", 0)) if previous and last else 0.0
            ring = ft.ProgressRing(
                value=max(0.0, min(1.0, score / 710.0)),
                width=136,
                height=136,
                stroke_width=9,
                color=TEAL,
                bgcolor="#E5EEF3",
            )
            gauge = ft.Stack(
                [
                    ring,
                    ft.Container(
                        width=136,
                        height=136,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            [
                                ft.Text("上次总分", size=10.5, color=FAINT),
                                ft.Text(
                                    fmt_score(score) if last else "—",
                                    size=32,
                                    weight=ft.FontWeight.W_700,
                                    color=INK,
                                    no_wrap=True,
                                ),
                                ft.Text("/ 710", size=10.5, color=FAINT),
                            ],
                            spacing=0,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                ],
                width=136,
                height=136,
            )
            if last:
                summary = ft.Column(
                    [
                        ft.Row(
                            [
                                pill(last.get("level", "CET-4"), bg=SKY, fg=INK_SOFT, size=10),
                                ft.Text(short_date(last.get("completed_at", "")), size=11, color=FAINT),
                            ],
                            spacing=8,
                        ),
                        ft.Text(
                            f"正确率 {percent(last.get('accuracy', 0))}",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=INK,
                        ),
                        ft.Text(
                            ("较上次 " + ("+" if delta >= 0 else "") + fmt_score(delta) + " 分")
                            if previous
                            else "这是你的第一份模考记录",
                            size=11.5,
                            color=SUCCESS if delta >= 0 else DANGER,
                        ),
                    ],
                    spacing=3,
                )
            else:
                summary = ft.Column(
                    [
                        ft.Text("还没有模考记录", size=13, weight=ft.FontWeight.W_600, color=INK),
                        body("完成第一套试卷后，这里会出现成绩趋势与薄弱项。", size=11.5),
                    ],
                    spacing=3,
                )
            inner = ft.Column(
                [
                    self._panel_header(
                        "最近状态",
                        "数据仅存本机",
                    ),
                    ft.Row(
                        [gauge, ft.Container(content=summary, expand=True, padding=ft.Padding.only(top=6))],
                        spacing=18,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    divider(),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(f"{self.stats['wrong_count']} 道", size=18, weight=ft.FontWeight.W_700, color=DANGER),
                                    ft.Text("待复习错题", size=11.5, color=MUTED),
                                ],
                                spacing=0,
                            ),
                            ft.Container(expand=True),
                            action_button(
                                "错题复习",
                                icon=ft.Icons.BOOKMARK_ROUNDED,
                                variant="secondary",
                                height=40,
                                font_size=12.5,
                                on_click=lambda: self.app.navigate("wrongbook"),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=14,
            )
        return glass_card(inner, padding=24, fill=0.64, col={"xs": 12, "lg": 4})

    def _panel_header(self, title: str, subtitle: str) -> ft.Control:
        return ft.Row(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=INK),
                ft.Container(expand=True),
                ft.Text(subtitle, size=10.5, color=FAINT, no_wrap=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ----------------------------------------------------------------- stats
    def _stats_row(self) -> ft.Control:
        return ft.ResponsiveRow(
            [
                _stat_card(
                    ft.Icons.FACT_CHECK_ROUNDED,
                    INDIGO_LIGHT,
                    INDIGO,
                    "完成模考",
                    str(self.stats["exam_count"]),
                    "EXAMS",
                ),
                _stat_card(
                    ft.Icons.INSIGHTS_ROUNDED,
                    MINT,
                    SUCCESS,
                    "平均正确率",
                    percent(self.stats["avg_accuracy"], 1),
                    "ACCURACY",
                ),
                _stat_card(
                    ft.Icons.BOOKMARK_ROUNDED,
                    BLUSH,
                    DANGER,
                    "待复习错题",
                    str(self.stats["wrong_count"]),
                    "REVIEW",
                ),
                _stat_card(
                    ft.Icons.EDIT_NOTE_ROUNDED,
                    SAND,
                    WARNING,
                    "累计练习",
                    str(self.stats["practice_attempts"]),
                    "PRACTICE",
                ),
            ],
            spacing=14,
            run_spacing=14,
        )

    def _section_header(self, title: str, subtitle: str) -> ft.Control:
        return ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(title, size=21, weight=ft.FontWeight.W_700, color=INK),
                        body(subtitle, size=12.5),
                    ],
                    spacing=2,
                    expand=True,
                ),
                pill("AUTO SAVED", icon=ft.Icons.DONE_ALL_ROUNDED, bg="#EDF5F1", fg=SUCCESS, size=10),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _features(self) -> ft.Control:
        return ft.ResponsiveRow(
            [
                _feature_card(
                    ft.Icons.HEADPHONES_ROUNDED,
                    "专项刷题",
                    "听力 · 阅读 · 翻译，一题一解析",
                    TEAL,
                    TEAL_LIGHT,
                    lambda: self.app.navigate("practice"),
                    "3 类",
                ),
                _feature_card(
                    ft.Icons.TIMER_ROUNDED,
                    "全真模拟",
                    "导入真题、音频计时、AI 阅卷",
                    INDIGO,
                    INDIGO_LIGHT,
                    lambda: self.app.navigate("exam"),
                    "55 题",
                ),
                _feature_card(
                    ft.Icons.BOOKMARK_ROUNDED,
                    "错题本",
                    "自动收录，重做直到真正掌握",
                    DANGER,
                    BLUSH,
                    lambda: self.app.navigate("wrongbook"),
                    f"{self.stats['wrong_count']} 道",
                ),
                _feature_card(
                    ft.Icons.INSIGHTS_ROUNDED,
                    "历史成绩",
                    "每次得分、单项分数与趋势",
                    WARNING,
                    SAND,
                    lambda: self.app.navigate("history"),
                    f"{self.stats['exam_count']} 次",
                ),
            ],
            spacing=14,
            run_spacing=14,
        )

    # ----------------------------------------------------------------- lower
    def _lower_grid(self) -> ft.Control:
        recent = self._recent_panel()
        pulse = self._pulse_panel()
        return ft.ResponsiveRow([recent, pulse], spacing=16, run_spacing=16)

    def _recent_panel(self) -> ft.Control:
        history = self.store.history()[:3]
        if history:
            rows: list[ft.Control] = []
            for idx, record in enumerate(history):
                if idx:
                    rows.append(divider())
                rows.append(self._recent_row(record))
            content = ft.Column(rows, spacing=10)
        else:
            content = empty_state(
                "还没有历史成绩",
                "完成一套全真模考，成绩会自动归档到这里。",
                icon=ft.Icons.INSIGHTS_ROUNDED,
                action=action_button(
                    "开始第一次模考",
                    icon=ft.Icons.PLAY_ARROW_ROUNDED,
                    variant="secondary",
                    height=40,
                    font_size=12.5,
                    on_click=lambda: self.app.navigate("exam"),
                ),
            )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("最近模考", size=17, weight=ft.FontWeight.W_700, color=INK),
                                    body("每一次分数都算数", size=11.5),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            text_action(
                                "查看全部",
                                lambda: self.app.navigate("history"),
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                size=12,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    content,
                ],
                spacing=14,
            ),
            padding=22,
            col={"xs": 12, "lg": 7},
        )

    def _recent_row(self, record: dict) -> ft.Control:
        score = fmt_score(record.get("score", 0))
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=44,
                        height=44,
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
                            ft.Text(record.get("level", "CET-4") + " 全真模考", size=13, weight=ft.FontWeight.W_600, color=INK),
                            ft.Text(
                                f"正确率 {percent(record.get('accuracy', 0))} · {full_date(record.get('completed_at', ''))}",
                                size=10.5,
                                color=FAINT,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(score, size=21, weight=ft.FontWeight.W_700, color=TEAL_DARK, no_wrap=True),
                            ft.Text("总分", size=9.5, color=FAINT, no_wrap=True),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=6, vertical=7),
            border_radius=12,
            on_click=lambda _e, r=record: self.app.show_history_detail(r),
            ink=True,
        )

    def _pulse_panel(self) -> ft.Control:
        practice = self.store.data.get("practice", {})
        by_cat = practice.get("by_category", {})
        bars: list[ft.Control] = []
        palette = {
            "listening": (TEAL, TEAL_LIGHT, ft.Icons.HEADPHONES_ROUNDED),
            "reading": (INDIGO, INDIGO_LIGHT, ft.Icons.MENU_BOOK_ROUNDED),
            "translation": (WARNING, SAND, ft.Icons.TRANSLATE_ROUNDED),
        }
        for category in ("listening", "reading", "translation"):
            attempts = int(by_cat.get(category, {}).get("attempts", 0))
            correct = int(by_cat.get(category, {}).get("correct", 0))
            rate = (correct / attempts * 100.0) if attempts else 0.0
            color, tint, icon = palette[category]
            bars.extend(
                [
                    ft.Row(
                        [
                            icon_box(icon, color=color, bg=tint, size=31, icon_size=15, radius=10),
                            ft.Text(CATEGORY_LABELS[category], size=12.5, weight=ft.FontWeight.W_600, color=INK),
                            ft.Container(expand=True),
                            ft.Text(
                                f"{attempts} 题 · {rate:.0f}%" if attempts else "尚未练习",
                                size=10.5,
                                color=FAINT,
                                no_wrap=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    progress_track(rate / 100.0 if attempts else 0.0, height=6, color=color, bg="#E9F0F4"),
                ]
            )
        tip = frosted_panel(
            ft.Row(
                [
                    icon_box(ft.Icons.LIGHTBULB_ROUNDED, color=WARNING, bg=WARNING_BG, size=38, icon_size=18, radius=12),
                    ft.Column(
                        [
                            ft.Text("今日建议", size=11, weight=ft.FontWeight.W_700, color=WARNING),
                            ft.Text(
                                "先做一套全真模考，系统会按听力 / 阅读 / 翻译拆出薄弱项。",
                                size=11.5,
                                color=INK_SOFT,
                                style=ft.TextStyle(height=1.45),
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=13,
            fill=0.46,
        )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("备考脉搏", size=17, weight=ft.FontWeight.W_700, color=INK),
                                    body("专项练习的正确率", size=11.5),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            pill("LOCAL DATA", bg="#EFF4F1", fg=SUCCESS, size=9.5),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Column(bars, spacing=8),
                    tip,
                    ft.Row(
                        [
                            ft.Text(
                                f"数据文件  {self.store.path.name}",
                                size=9.5,
                                color=FAINT,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                            ft.Container(
                                content=pill("AI 设置", bg=INDIGO_LIGHT, fg=INDIGO, size=9),
                                on_click=lambda _e: self.app.show_ai_settings(),
                                tooltip="配置 AI API",
                                ink=True,
                                border_radius=999,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=13,
            ),
            padding=22,
            col={"xs": 12, "lg": 5},
        )

    def _footer(self) -> ft.Control:
        return ft.Row(
            [
                ft.Icon(ft.Icons.SHIELD_ROUNDED, size=13, color=FAINT),
                ft.Text("无需登录 · 无后端 · 所有答题记录保存在本地 JSON", size=10.5, color=FAINT),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        )
