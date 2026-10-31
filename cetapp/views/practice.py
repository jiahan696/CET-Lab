from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ..questions import CATEGORY_LABELS
from ..scoring import is_correct
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
from ..utils import percent
from .qcomponents import (
    answer_text,
    explanation_block,
    material_block,
    option_item,
    question_meta_line,
    question_prompt,
)

if TYPE_CHECKING:
    from ..app import CETApp


CATEGORY_META = {
    "listening": {
        "icon": ft.Icons.HEADPHONES_ROUNDED,
        "color": TEAL,
        "tint": TEAL_LIGHT,
        "title": "听力理解",
        "desc": "短对话 · 长对话 · 新闻与讲座",
        "tip": "先抓取对话中的转折词和最后一句，答案往往藏在说话人的真实意图里。",
    },
    "reading": {
        "icon": ft.Icons.MENU_BOOK_ROUNDED,
        "color": INDIGO,
        "tint": INDIGO_LIGHT,
        "title": "阅读理解",
        "desc": "仔细阅读 · 多项选择",
        "tip": "先读题干定位关键词，再回原文找同义替换；不要凭常识代替原文。",
    },
    "translation": {
        "icon": ft.Icons.TRANSLATE_ROUNDED,
        "color": WARNING,
        "tint": SAND,
        "title": "翻译辨析",
        "desc": "译文选择 · 表达判断",
        "tip": "先判断主干和逻辑关系，再检查冠词、时态、介词和搭配是否自然。",
    },
}


class PracticeView:
    full_screen = False

    def __init__(self, app: "CETApp", category: str | None = None) -> None:
        self.app = app
        self.store = app.store
        self.category = category if category in CATEGORY_META else "listening"
        self.level = "全部"
        self.index = 0
        self.selection: list[str] = []
        self.revealed = False
        self.last_ok = False
        self.finished = False
        self.round_attempts = 0
        self.round_correct = 0
        self.queue = self._filtered()

    # ------------------------------------------------------------------ data
    def _filtered(self) -> list[dict]:
        rows = [
            q
            for q in self.app.questions
            if q.get("category") == self.category
            and (self.level == "全部" or q.get("level") == self.level)
        ]
        return rows

    @property
    def current(self) -> dict | None:
        if not self.queue:
            return None
        return self.queue[min(self.index, len(self.queue) - 1)]

    def _reset_round(self, *, keep_index: bool = False) -> None:
        if not keep_index:
            self.index = 0
        self.selection = []
        self.revealed = False
        self.last_ok = False
        self.finished = False
        self.round_attempts = 0
        self.round_correct = 0
        self.queue = self._filtered()
        if self.index >= len(self.queue):
            self.index = 0

    # ----------------------------------------------------------------- build
    def build(self) -> ft.Control:
        header = self._header()
        controls = self._controls()
        if self.finished:
            return ft.Column([header, controls, self._completion()], spacing=16)
        if not self.queue:
            return ft.Column(
                [
                    header,
                    controls,
                    glass_card(
                        empty_state(
                            "当前筛选下没有题目",
                            "换一个级别或题型继续练习。",
                            icon=ft.Icons.FILTER_ALT_OFF_ROUNDED,
                            action=action_button(
                                "重置筛选",
                                variant="secondary",
                                height=40,
                                font_size=12.5,
                                on_click=self._reset_filters,
                            ),
                        ),
                        padding=12,
                    ),
                ],
                spacing=16,
            )
        return ft.Column(
            [
                header,
                controls,
                ft.ResponsiveRow(
                    [self._question_card(), self._side_panel()],
                    spacing=16,
                    run_spacing=16,
                ),
            ],
            spacing=16,
        )

    def _header(self) -> ft.Control:
        stats = self.store.stats()
        return ft.Row(
            [
                ft.Column(
                    [
                        eyebrow("PRACTICE STUDIO · 专项训练"),
                        heading("专项刷题", size=27),
                        body("做完一题，立即查看标准答案与详细解析。", size=12.5),
                    ],
                    spacing=2,
                    expand=True,
                ),
                pill(f"{stats['practice_attempts']} 次练习", icon=ft.Icons.EDIT_NOTE_ROUNDED, bg=TEAL_LIGHT, fg=TEAL_DARK),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def _controls(self) -> ft.Control:
        category_tabs = ft.Row(
            [
                self._category_tab(cat)
                for cat in ("listening", "reading", "translation")
            ],
            spacing=8,
        )
        level_tabs = ft.Row(
            [
                self._level_tab("全部"),
                self._level_tab("CET-4"),
                self._level_tab("CET-6"),
            ],
            spacing=6,
        )
        return glass_card(
            ft.Column(
                [
                    category_tabs,
                    ft.Row(
                        [
                            ft.Text("难度范围", size=10, color=FAINT),
                            level_tabs,
                            ft.Container(expand=True),
                            ft.Text(f"{len(self.queue)} 道题可练", size=10.5, color=FAINT, no_wrap=True),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
            ),
            padding=14,
            radius=18,
            fill=0.56,
        )

    def _category_tab(self, category: str) -> ft.Container:
        meta = CATEGORY_META[category]
        active = category == self.category
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(meta["icon"], size=15, color=WHITE if active else meta["color"]),
                    ft.Text(
                        CATEGORY_LABELS[category],
                        size=12.5,
                        weight=ft.FontWeight.W_700,
                        color=WHITE if active else INK_SOFT,
                        no_wrap=True,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        str(sum(1 for q in self.app.questions if q.get("category") == category)),
                        size=9.5,
                        color="#D9F0EC" if active else FAINT,
                        no_wrap=True,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=11),
            bgcolor=meta["color"] if active else ft.Colors.with_opacity(0.44, WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.55, WHITE)) if active else ft.Border.all(1, LINE_SOFT),
            border_radius=13,
            expand=True,
            on_click=lambda _e, c=category: self._switch_category(c),
            ink=True,
        )

    def _level_tab(self, level: str) -> ft.Container:
        active = level == self.level
        label = "全部" if level == "全部" else level.replace("CET-", "四级" if level == "CET-4" else "六级")
        return ft.Container(
            content=ft.Text(
                label,
                size=10.5,
                color=WHITE if active else MUTED,
                weight=ft.FontWeight.W_600,
                no_wrap=True,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            bgcolor=TEAL if active else ft.Colors.with_opacity(0.4, WHITE),
            border_radius=999,
            on_click=lambda _e, lv=level: self._switch_level(lv),
            ink=True,
        )

    def _switch_category(self, category: str) -> None:
        if category == self.category:
            return
        self.category = category
        self._reset_round()
        self.app.render()

    def _switch_level(self, level: str) -> None:
        if level == self.level:
            return
        self.level = level
        self._reset_round()
        self.app.render()

    def _reset_filters(self) -> None:
        self.level = "全部"
        self._reset_round()
        self.app.render()

    # --------------------------------------------------------------- question
    def _question_card(self) -> ft.Control:
        q = self.current
        assert q is not None
        answer = self.selection
        options = []
        for i, text in enumerate(q.get("options", [])):
            key = chr(65 + i)
            status = "idle"
            if self.revealed:
                if key in q.get("answers", []):
                    status = "correct"
                elif key in answer:
                    status = "wrong"
            options.append(
                option_item(
                    key,
                    text,
                    selected=key in answer,
                    on_click=self._choose,
                    status=status,
                    disabled=self.revealed,
                )
            )
        meta = CATEGORY_META[self.category]
        content_controls: list[ft.Control] = [
            ft.Row(
                [
                    ft.Row(
                        [
                            icon_box(meta["icon"], color=meta["color"], bg=meta["tint"], size=36, icon_size=17, radius=11),
                            ft.Column(
                                [
                                    ft.Text(meta["title"], size=14, weight=ft.FontWeight.W_700, color=INK),
                                    ft.Text(
                                        f"{q.get('level')} · {q.get('difficulty', '进阶')}",
                                        size=9.5,
                                        color=FAINT,
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        f"{self.index + 1:02d} / {len(self.queue):02d}",
                        size=10,
                        color=FAINT,
                        no_wrap=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            progress_track(
                (self.index + (1 if self.revealed else 0)) / max(1, len(self.queue)),
                height=4,
                color=meta["color"],
            ),
            divider(),
            material_block(
                q,
                compact=True,
                on_select=lambda text: self.app.translate_selection(
                    text, source=f"{CATEGORY_LABELS.get(self.category, self.category)}练习"
                ),
            ),
            question_prompt(q),
            ft.Text(
                "多选题：选出所有正确答案。" if q.get("type") == "multiple" else "请选择一个最符合题意的选项。",
                size=10.5,
                color=FAINT,
            ),
            ft.Column(options, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        ]
        if self.revealed:
            content_controls.append(
                explanation_block(q, answer, is_ok=self.last_ok)
            )
            content_controls.append(
                ft.Row(
                    [
                        text_action(
                            "换一题",
                            self._next_question,
                            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                            size=11.5,
                        ),
                        ft.Container(expand=True),
                        action_button(
                            "完成本轮" if self.index >= len(self.queue) - 1 else "下一题",
                            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                            height=42,
                            font_size=12.5,
                            on_click=self._next_question,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        else:
            content_controls.append(
                ft.Row(
                    [
                        text_action(
                            "跳过本题",
                            self._next_question,
                            icon=ft.Icons.SKIP_NEXT_ROUNDED,
                            color=FAINT,
                            size=11.5,
                        ),
                        ft.Container(expand=True),
                        action_button(
                            "提交答案",
                            icon=ft.Icons.CHECK_ROUNDED,
                            height=42,
                            font_size=12.5,
                            on_click=self._submit_answer,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        return glass_card(
            ft.Column(content_controls, spacing=13),
            padding=22,
            col={"xs": 12, "lg": 8},
        )

    def _side_panel(self) -> ft.Control:
        meta = CATEGORY_META[self.category]
        stats = self.store.stats()
        practice = self.store.data.get("practice", {}).get("by_category", {}).get(self.category, {})
        attempts = int(practice.get("attempts", 0))
        correct = int(practice.get("correct", 0))
        rate = (correct / attempts * 100.0) if attempts else 0.0
        correct_in_round = self.round_correct
        round_rate = (correct_in_round / self.round_attempts * 100.0) if self.round_attempts else 0.0
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("本轮状态", size=16, weight=ft.FontWeight.W_700, color=INK),
                            ft.Container(expand=True),
                            pill(
                                f"已做 {self.round_attempts} 题",
                                bg=meta["tint"],
                                fg=meta["color"],
                                size=10,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            f"{round_rate:.0f}%",
                                            size=32,
                                            weight=ft.FontWeight.W_800,
                                            color=meta["color"],
                                            no_wrap=True,
                                        ),
                                        ft.Container(expand=True),
                                        ft.Column(
                                            [
                                                ft.Text(f"累计 {attempts} 题", size=10, color=FAINT),
                                                ft.Text(f"正确率 {rate:.0f}%", size=11, color=INK_SOFT, weight=ft.FontWeight.W_600),
                                            ],
                                            spacing=1,
                                            horizontal_alignment=ft.CrossAxisAlignment.END,
                                        ),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.END,
                                ),
                                progress_track((correct_in_round / max(1, self.round_attempts)) if self.round_attempts else 0, height=6, color=meta["color"]),
                                ft.Text("本轮正确率", size=9.5, color=FAINT),
                            ],
                            spacing=7,
                        ),
                        padding=14,
                        bgcolor=ft.Colors.with_opacity(0.44, WHITE),
                        border=ft.Border.all(1, LINE_SOFT),
                        border_radius=15,
                    ),
                    divider(),
                    ft.Row(
                        [
                            icon_box(ft.Icons.BOOKMARK_ROUNDED, color=DANGER, bg=BLUSH, size=36, icon_size=17, radius=11),
                            ft.Column(
                                [
                                    ft.Text(f"{stats['wrong_count']} 道错题", size=13, weight=ft.FontWeight.W_700, color=INK),
                                    ft.Text("做错的题会自动收录", size=9.5, color=FAINT),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                            text_action(
                                "去复习",
                                lambda: self.app.navigate("wrongbook"),
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                size=10.5,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=9,
                    ),
                    divider(),
                    ft.Row(
                        [
                            icon_box(ft.Icons.LIGHTBULB_ROUNDED, color=WARNING, bg=SAND, size=32, icon_size=15, radius=10),
                            ft.Text(
                                meta["tip"],
                                size=10.5,
                                color=INK_SOFT,
                                style=ft.TextStyle(height=1.55),
                                expand=True,
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    frosted_panel(
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=15, color=INDIGO),
                                ft.Text(
                                    "AI 深度讲解接口已预留",
                                    size=10,
                                    color=INDIGO,
                                    weight=ft.FontWeight.W_600,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=10,
                        fill=0.38,
                    ),
                ],
                spacing=12,
            ),
            padding=20,
            col={"xs": 12, "lg": 4},
            fill=0.62,
        )

    def _completion(self) -> ft.Control:
        total = self.round_attempts
        rate = (self.round_correct / total * 100.0) if total else 0.0
        meta = CATEGORY_META[self.category]
        return ft.Row(
            [
                glass_card(
                    ft.Column(
                        [
                            icon_box(ft.Icons.FACT_CHECK_ROUNDED, color=SUCCESS, bg=SUCCESS_BG, size=54, icon_size=26, radius=18),
                            heading("本轮完成", 26),
                            body(
                                f"完成 {total} 题，答对 {self.round_correct} 题，正确率 {rate:.0f}%。",
                                13,
                            ),
                            ft.Row(
                                [
                                    action_button(
                                        "再来一轮",
                                        icon=ft.Icons.REPLAY_ROUNDED,
                                        on_click=self._restart,
                                    ),
                                    action_button(
                                        "切换题型",
                                        variant="secondary",
                                        on_click=lambda: self.app.navigate("practice"),
                                    ),
                                    action_button(
                                        "查看错题",
                                        variant="secondary",
                                        on_click=lambda: self.app.navigate("wrongbook"),
                                    ),
                                ],
                                spacing=10,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ],
                        spacing=13,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=30,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ]
        )

    # ---------------------------------------------------------------- actions
    def _choose(self, key: str) -> None:
        if self.revealed:
            return
        q = self.current
        if not q:
            return
        if q.get("type") == "multiple":
            if key in self.selection:
                self.selection.remove(key)
            else:
                self.selection.append(key)
        else:
            self.selection = [key]
        self.app.render()

    def _submit_answer(self) -> None:
        q = self.current
        if not q or self.revealed:
            return
        if not self.selection:
            self.app.notify("请先选择答案。", "warning")
            return
        ok = is_correct(q, self.selection)
        self.revealed = True
        self.last_ok = ok
        self.round_attempts += 1
        if ok:
            self.round_correct += 1
        self.store.record_practice(self.category, ok)
        if not ok:
            self.store.add_wrong(q, self.selection, "practice")
            self.app.notify("回答错误，已自动加入错题本。", "warning")
        else:
            self.app.notify("回答正确。", "success")
        self.app.render()

    def _next_question(self) -> None:
        if not self.queue:
            return
        if self.index >= len(self.queue) - 1:
            self.finished = True
            self.revealed = False
            self.selection = []
            self.app.render()
            return
        self.index += 1
        self.selection = []
        self.revealed = False
        self.last_ok = False
        self.app.render()

    def _restart(self) -> None:
        self._reset_round()
        self.app.render()
