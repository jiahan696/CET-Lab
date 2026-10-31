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
    text_action,
)
from ..utils import full_date, short_date
from .qcomponents import (
    answer_text,
    explanation_block,
    material_block,
    option_item,
    question_prompt,
)

if TYPE_CHECKING:
    from ..app import CETApp


CATEGORY_STYLE = {
    "listening": (TEAL, TEAL_LIGHT, ft.Icons.HEADPHONES_ROUNDED),
    "reading": (INDIGO, INDIGO_LIGHT, ft.Icons.MENU_BOOK_ROUNDED),
    "translation": (WARNING, SAND, ft.Icons.TRANSLATE_ROUNDED),
}


class WrongbookView:
    full_screen = False

    def __init__(self, app: "CETApp") -> None:
        self.app = app
        self.store = app.store

    def build(self) -> ft.Control:
        items = self._items()
        header = ft.Row(
            [
                ft.Column(
                    [
                        eyebrow("REVIEW DESK · 错题复盘"),
                        heading("错题本", size=27),
                        body("做错的题自动收录。重做、移除，或清空后重新开始。", size=12.5),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Column(
                    [
                        pill(
                            f"{len(items)} 道待复习",
                            icon=ft.Icons.BOOKMARK_ROUNDED,
                            bg=BLUSH,
                            fg=DANGER,
                        ),
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
                if items
                else pill("0 道待复习", icon=ft.Icons.DONE_ALL_ROUNDED, bg=SUCCESS_BG, fg=SUCCESS),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        summary = self._summary(items)
        if not items:
            content = glass_card(
                empty_state(
                    "错题本还是空的",
                    "专项刷题或模考中答错的题会自动出现在这里。",
                    icon=ft.Icons.BOOKMARK_BORDER_ROUNDED,
                    action=ft.Row(
                        [
                            action_button(
                                "去专项刷题",
                                icon=ft.Icons.EDIT_NOTE_ROUNDED,
                                on_click=lambda: self.app.navigate("practice"),
                            ),
                            action_button(
                                "开始模考",
                                variant="secondary",
                                on_click=lambda: self.app.navigate("exam"),
                            ),
                        ],
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ),
                padding=16,
            )
        else:
            cards = [self._card(item, self._question(item)) for item in items]
            content = ft.Column(cards, spacing=12)
        return ft.Column([header, summary, content], spacing=16)

    def _items(self) -> list[dict]:
        by_id = {q["id"]: q for q in self.app.questions}
        for paper in self.app.library.papers:
            for q in self.app.library_questions(paper):
                by_id[q["id"]] = q
        items = [item for item in self.store.wrong_items() if item.get("question_id") in by_id]
        return items

    def _question(self, item: dict) -> dict:
        qid = item.get("question_id")
        for q in self.app.questions:
            if q["id"] == qid:
                return q
        for paper in self.app.library.papers:
            for q in self.app.library_questions(paper):
                if q["id"] == qid:
                    return q
        raise StopIteration(qid)

    def _summary(self, items: list[dict]) -> ft.Control:
        counts = {cat: 0 for cat in CATEGORY_STYLE}
        for item in items:
            try:
                q = self._question(item)
                counts[q["category"]] += 1
            except StopIteration:
                pass
        cells = []
        for category, (color, tint, icon) in CATEGORY_STYLE.items():
            cells.append(
                ft.Container(
                    content=ft.Row(
                        [
                            icon_box(icon, color=color, bg=tint, size=32, icon_size=15, radius=10),
                            ft.Column(
                                [
                                    ft.Text(CATEGORY_LABELS[category], size=10, color=FAINT),
                                    ft.Text(f"{counts[category]} 道", size=15, weight=ft.FontWeight.W_700, color=INK),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=9),
                    bgcolor=ft.Colors.with_opacity(0.44, WHITE),
                    border=ft.Border.all(1, LINE_SOFT),
                    border_radius=13,
                    expand=True,
                )
            )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.INSIGHTS_ROUNDED, size=15, color=TEAL),
                            ft.Text("错题分布", size=11, weight=ft.FontWeight.W_700, color=INK),
                            ft.Container(expand=True),
                            ft.Text(
                                "点击「重做」立即开始",
                                size=9.5,
                                color=FAINT,
                                no_wrap=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(cells, spacing=8),
                ],
                spacing=11,
            ),
            padding=14,
            radius=18,
            fill=0.58,
        )

    def _card(self, item: dict, question: dict) -> ft.Control:
        category = question.get("category", "reading")
        color, tint, icon = CATEGORY_STYLE.get(category, (TEAL, TEAL_LIGHT, ft.Icons.BOOKMARK_ROUNDED))
        wrong_count = int(item.get("wrong_count", 1))
        meta = ft.Row(
            [
                pill(CATEGORY_LABELS.get(category, category), bg=tint, fg=color, size=9.5),
                pill(question.get("level", "CET-4"), bg=SKY, fg=INK_SOFT, size=9.5),
                ft.Text(
                    f"错 {wrong_count} 次",
                    size=10,
                    color=DANGER,
                    weight=ft.FontWeight.W_600,
                    no_wrap=True,
                ),
                ft.Container(expand=True),
                ft.Text(
                    short_date(item.get("last_wrong_at", "")),
                    size=9.5,
                    color=FAINT,
                    no_wrap=True,
                ),
            ],
            spacing=7,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(icon, color=color, bg=tint, size=38, icon_size=18, radius=12),
                            ft.Column(
                                [
                                    meta,
                                    ft.Text(
                                        question.get("question", ""),
                                        size=14.5,
                                        weight=ft.FontWeight.W_600,
                                        color=INK,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        style=ft.TextStyle(height=1.45),
                                    ),
                                ],
                                spacing=6,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    divider(),
                    ft.Row(
                        [
                            ft.Text(
                                f"上次答案  {answer_text(item.get('last_answer'))}",
                                size=10,
                                color=FAINT,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                            text_action(
                                "移除",
                                lambda q=question: self._confirm_remove(q),
                                icon=ft.Icons.CLOSE_ROUNDED,
                                color=FAINT,
                                size=11,
                            ),
                            action_button(
                                "重做本题",
                                icon=ft.Icons.REPLAY_ROUNDED,
                                variant="secondary",
                                height=36,
                                font_size=11.5,
                                on_click=lambda q=question: self._open_redo(q),
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=11,
            ),
            padding=17,
        )

    # ---------------------------------------------------------------- actions
    def _confirm_remove(self, question: dict) -> None:
        def remove() -> None:
            self.store.remove_wrong(question["id"])
            self.app.render()
            self.app.notify("已从错题本移除。", "success")

        self.app.confirm(
            "移除这道错题？",
            f"将从错题本中移除「{question.get('question', '')[:40]}…」。之后仍可再次练习。",
            confirm_label="移除",
            danger=True,
            on_confirm=remove,
        )

    def _confirm_clear(self) -> None:
        def clear() -> None:
            self.store.clear_wrong()
            self.app.render()
            self.app.notify("错题本已全部清空。", "success")

        self.app.confirm(
            "清空全部错题？",
            "所有错题记录将被删除，此操作不可撤销。你的历史成绩与练习记录不会受影响。",
            confirm_label="全部清空",
            danger=True,
            on_confirm=clear,
        )

    # ------------------------------------------------------------------ redo
    def _open_redo(self, question: dict) -> None:
        state: dict = {"selection": [], "revealed": False, "ok": False}
        content_host = ft.Container()
        dialog_holder: dict = {"dialog": None}

        def close() -> None:
            self.app.page.pop_dialog()
            self.app.render()

        def choose(key: str) -> None:
            if state["revealed"]:
                return
            if question.get("type") == "multiple":
                if key in state["selection"]:
                    state["selection"].remove(key)
                else:
                    state["selection"].append(key)
            else:
                state["selection"] = [key]
            refresh()

        def submit() -> None:
            if state["revealed"]:
                return
            if not state["selection"]:
                self.app.notify("请先选择答案。", "warning")
                return
            ok = is_correct(question, state["selection"])
            state["revealed"] = True
            state["ok"] = ok
            self.store.note_redo(question["id"])
            self.store.record_practice(question.get("category", "reading"), ok)
            if not ok:
                self.store.add_wrong(question, state["selection"], "wrongbook")
            refresh()

        def remove() -> None:
            self.store.remove_wrong(question["id"])
            self.app.page.pop_dialog()
            self.app.render()
            self.app.notify("已掌握，题目已移出错题本。", "success")

        def again() -> None:
            state["selection"] = []
            state["revealed"] = False
            state["ok"] = False
            refresh()

        def refresh() -> None:
            options = []
            for i, text in enumerate(question.get("options", [])):
                key = chr(65 + i)
                status = "idle"
                if state["revealed"]:
                    if key in question.get("answers", []):
                        status = "correct"
                    elif key in state["selection"]:
                        status = "wrong"
                options.append(
                    option_item(
                        key,
                        text,
                        selected=key in state["selection"],
                        on_click=choose,
                        status=status,
                        disabled=state["revealed"],
                    )
                )
            children: list[ft.Control] = [
                ft.Row(
                    [
                        pill(
                            CATEGORY_LABELS.get(question.get("category", ""), ""),
                            bg=TEAL_LIGHT,
                            fg=TEAL_DARK,
                            size=9.5,
                        ),
                        pill(question.get("level", "CET-4"), bg=SKY, fg=INK_SOFT, size=9.5),
                        ft.Container(expand=True),
                        ft.Text(
                            f"第 {question.get('number', '')} 题 · 重做",
                            size=9.5,
                            color=FAINT,
                        ),
                    ],
                    spacing=7,
                ),
                material_block(question, compact=True),
                question_prompt(question),
                ft.Text(
                    "多选题：选出所有正确答案。" if question.get("type") == "multiple" else "请选择一个选项。",
                    size=10,
                    color=FAINT,
                ),
                ft.Column(options, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            ]
            if state["revealed"]:
                children.append(
                    explanation_block(question, state["selection"], is_ok=state["ok"])
                )
                actions = [
                    action_button(
                        "再练一次",
                        variant="secondary",
                        height=38,
                        font_size=11.5,
                        width=104,
                        on_click=again,
                    )
                ]
                if state["ok"]:
                    actions.append(
                        action_button(
                            "移出错题本",
                            icon=ft.Icons.DONE_ALL_ROUNDED,
                            height=38,
                            font_size=11.5,
                            width=128,
                            on_click=remove,
                        )
                    )
                actions.append(
                    action_button(
                        "关闭",
                        variant="secondary",
                        height=38,
                        font_size=11.5,
                        width=86,
                        on_click=close,
                    )
                )
            else:
                actions = [
                    action_button(
                        "关闭",
                        variant="secondary",
                        height=38,
                        font_size=11.5,
                        width=86,
                        on_click=close,
                    )
                ]
            if state["revealed"] is False:
                children.append(
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            action_button(
                                "提交答案",
                                icon=ft.Icons.CHECK_ROUNDED,
                                height=40,
                                font_size=12,
                                on_click=submit,
                            ),
                        ]
                    )
                )
            content_host.content = ft.Column(children, spacing=12)
            if dialog_holder.get("dialog") is not None:
                dialog_holder["dialog"].actions = actions
            try:
                self.app.page.update()
            except Exception:
                pass

        dialog = ft.AlertDialog(
            modal=True,
            scrollable=True,
            bgcolor=ft.Colors.with_opacity(0.98, WHITE),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Row(
                [
                    icon_box(ft.Icons.REPLAY_ROUNDED, color=TEAL, bg=TEAL_LIGHT, size=36, icon_size=17, radius=11),
                    ft.Text("错题重做", size=18, weight=ft.FontWeight.W_700, color=INK),
                ],
                spacing=10,
            ),
            content=ft.Container(
                width=self.app._dialog_width(620),
                content=content_host,
            ),
            actions=[],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dialog_holder["dialog"] = dialog
        refresh()
        self.app.page.show_dialog(dialog)
