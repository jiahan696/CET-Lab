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
    text_action,
)
from ..utils import full_date, short_date

if TYPE_CHECKING:
    from ..app import CETApp


class WordbookView:
    full_screen = False

    def __init__(self, app: "CETApp") -> None:
        self.app = app
        self.store = app.store

    def build(self) -> ft.Control:
        words = self.store.words()
        header = ft.Row(
            [
                ft.Column(
                    [
                        eyebrow("WORD DESK · 单词本"),
                        heading("单词本", size=27),
                        body("阅读时划词，AI 翻译后一键收藏；在这里集中复习。", size=12.5),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Column(
                    [
                        pill(f"{len(words)} 个词条", icon=ft.Icons.MENU_BOOK_ROUNDED, bg=TEAL_LIGHT, fg=TEAL_DARK),
                        action_button(
                            "清空全部",
                            icon=ft.Icons.DELETE_SWEEP_ROUNDED,
                            variant="danger",
                            height=36,
                            font_size=11.5,
                            on_click=self._confirm_clear,
                        ),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                )
                if words
                else pill("0 个词条", icon=ft.Icons.MENU_BOOK_ROUNDED, bg=SKY, fg=INDIGO),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        if not words:
            content = glass_card(
                empty_state(
                    "单词本还是空的",
                    "在模考阅读、翻译原文或刷题材料中选中英文，AI 翻译面板里可以加入单词本。",
                    icon=ft.Icons.MENU_BOOK_ROUNDED,
                    action=ft.Row(
                        [
                            action_button(
                                "去刷题",
                                icon=ft.Icons.EDIT_NOTE_ROUNDED,
                                on_click=lambda: self.app.navigate("practice"),
                            ),
                            action_button(
                                "AI 设置",
                                variant="secondary",
                                icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                                on_click=self.app.show_ai_settings,
                            ),
                        ],
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ),
                padding=16,
            )
        else:
            content = ft.Column([self._card(word) for word in words], spacing=12)
        return ft.Column([header, self._summary(words), content], spacing=16)

    def _summary(self, words: list[dict]) -> ft.Control:
        sources = len({w.get("source", "") for w in words if w.get("source")})
        latest = words[0].get("added_at", "") if words else ""
        cells = [
            self._stat("词条总数", str(len(words)), TEAL, TEAL_LIGHT, ft.Icons.MENU_BOOK_ROUNDED),
            self._stat("来源试卷", str(sources) if sources else "—", INDIGO, INDIGO_LIGHT, ft.Icons.ARTICLE_ROUNDED),
            self._stat("最近添加", short_date(latest) if latest else "—", WARNING, SAND, ft.Icons.SCHEDULE_ROUNDED),
        ]
        return ft.ResponsiveRow(cells, spacing=14, run_spacing=14)

    def _stat(self, label: str, value: str, color: str, tint: str, icon: ft.IconData) -> ft.Control:
        return glass_card(
            ft.Row(
                [
                    icon_box(icon, color=color, bg=tint, size=38, icon_size=18, radius=12),
                    ft.Column(
                        [
                            ft.Text(value, size=20, weight=ft.FontWeight.W_700, color=INK, no_wrap=True),
                            ft.Text(label, size=10.5, color=FAINT, no_wrap=True),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=15,
            col={"xs": 12, "sm": 4},
        )

    def _card(self, word: dict) -> ft.Control:
        term = word.get("term", "")
        translation = word.get("translation", "")
        meta = " ".join(
            x for x in [word.get("part_of_speech", ""), word.get("phonetic", "")] if x
        )
        context = word.get("context", "")
        source = word.get("source", "")
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.TRANSLATE_ROUNDED, color=TEAL, bg=TEAL_LIGHT, size=40, icon_size=18, radius=13),
                            ft.Column(
                                [
                                    ft.Text(term, size=18, weight=ft.FontWeight.W_700, color=INK, selectable=True),
                                    *([ft.Text(meta, size=10, color=FAINT)] if meta else []),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.Column(
                                [
                                    ft.Text(short_date(word.get("added_at", "")), size=9.5, color=FAINT),
                                    ft.Text(f"查询 {word.get('lookup_count', 1)} 次", size=9, color=FAINT),
                                ],
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Text(translation, size=13, color=INK_SOFT, selectable=True, style=ft.TextStyle(height=1.6)),
                    *(
                        [
                            frosted_panel(
                                ft.Text(
                                    f"原文：{context[:220]}",
                                    size=10.5,
                                    color=MUTED,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    selectable=True,
                                ),
                                padding=10,
                                fill=0.38,
                            )
                        ]
                        if context
                        else []
                    ),
                    *(
                        [
                            ft.Text(
                                f"例句：{word.get('example')}",
                                size=10.5,
                                color=INK_SOFT,
                                selectable=True,
                            )
                        ]
                        if word.get("example")
                        else []
                    ),
                    divider(),
                    ft.Row(
                        [
                            ft.Text(f"来源：{source or '划词翻译'}", size=9.5, color=FAINT, expand=True),
                            text_action(
                                "移除",
                                lambda w=word: self._remove(w),
                                icon=ft.Icons.CLOSE_ROUNDED,
                                color=FAINT,
                                size=10.5,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
            ),
            padding=17,
        )

    def _remove(self, word: dict) -> None:
        self.store.remove_word(word.get("id", ""))
        self.app.render()
        self.app.notify("已从单词本移除。", "success")

    def _confirm_clear(self) -> None:
        def clear() -> None:
            self.store.clear_words()
            self.app.render()
            self.app.notify("单词本已清空。", "success")

        self.app.confirm(
            "清空单词本？",
            "所有已收藏的单词和翻译将被删除，此操作不可撤销。",
            confirm_label="全部清空",
            danger=True,
            on_confirm=clear,
        )
