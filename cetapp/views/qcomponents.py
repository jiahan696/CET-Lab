from __future__ import annotations

from typing import Any

import flet as ft

from ..questions import CATEGORY_LABELS, section_cn, section_name
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
    MUTED,
    SKY,
    SUCCESS,
    SUCCESS_BG,
    TEAL,
    TEAL_DARK,
    TEAL_LIGHT,
    WARNING,
    WHITE,
    body,
    frosted_panel,
    icon_box,
    pill,
    selectable_text,
)


def answer_text(answer: list[str] | None) -> str:
    if not answer:
        return "未作答"
    return " / ".join(str(a).upper() for a in sorted(answer))


def option_item(
    key: str,
    text: str,
    *,
    selected: bool = False,
    on_click=None,
    status: str = "idle",
    disabled: bool = False,
) -> ft.Container:
    """A large, touch-friendly option row.

    status: idle | correct | wrong. `selected` controls the teal "picked" state.
    """
    if status == "correct":
        bg = SUCCESS_BG
        border = ft.Border.all(1.4, SUCCESS)
        badge_bg = SUCCESS
        badge_fg = WHITE
        text_color = "#215E4A"
        trailing = ft.Icon(ft.Icons.CHECK_ROUNDED, size=18, color=SUCCESS)
    elif status == "wrong":
        bg = DANGER_BG
        border = ft.Border.all(1.4, DANGER)
        badge_bg = DANGER
        badge_fg = WHITE
        text_color = "#843F4A"
        trailing = ft.Icon(ft.Icons.CLOSE_ROUNDED, size=18, color=DANGER)
    elif selected:
        bg = ft.Colors.with_opacity(0.86, TEAL_LIGHT)
        border = ft.Border.all(1.3, TEAL)
        badge_bg = TEAL
        badge_fg = WHITE
        text_color = INK
        trailing = ft.Icon(ft.Icons.CHECK_ROUNDED, size=17, color=TEAL)
    else:
        bg = ft.Colors.with_opacity(0.54, WHITE)
        border = ft.Border.all(1, "#DDE8F2")
        badge_bg = "#EDF3F8"
        badge_fg = INK_SOFT
        text_color = INK_SOFT
        trailing = None

    controls: list[ft.Control] = [
        ft.Container(
            width=28,
            height=28,
            border_radius=9,
            bgcolor=badge_bg,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(
                key,
                size=12,
                color=badge_fg,
                weight=ft.FontWeight.W_700,
                no_wrap=True,
            ),
        ),
        ft.Container(
            expand=True,
            content=ft.Text(
                text,
                size=13.5,
                color=text_color,
                weight=ft.FontWeight.W_500,
                style=ft.TextStyle(height=1.5),
                selectable=True,
            ),
        ),
    ]
    if trailing:
        controls.append(trailing)
    return ft.Container(
        content=ft.Row(
            controls,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=13),
        bgcolor=bg,
        border=border,
        border_radius=15,
        on_click=(lambda _e: on_click(key)) if (on_click and not disabled) else None,
        ink=bool(on_click and not disabled and status == "idle" and not selected),
        animate=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        opacity=1.0 if not disabled or status != "idle" else 0.82,
    )


def material_block(
    question: dict[str, Any],
    *,
    compact: bool = False,
    on_select=None,
) -> ft.Control:
    category = question.get("category")
    label, icon = {
        "listening": ("LISTENING SCRIPT · 听力材料", ft.Icons.HEADPHONES_ROUNDED),
        "reading": ("READING PASSAGE · 阅读材料", ft.Icons.MENU_BOOK_ROUNDED),
        "translation": ("SOURCE TEXT · 中文原文", ft.Icons.TRANSLATE_ROUNDED),
    }.get(category, ("MATERIAL", ft.Icons.ARTICLE_ROUNDED))
    meta: list[ft.Control] = [
        ft.Icon(icon, size=14, color=TEAL),
        ft.Text(
            label,
            size=9.5,
            color=TEAL_DARK,
            weight=ft.FontWeight.W_700,
            no_wrap=True,
        ),
        ft.Container(expand=True),
    ]
    if category == "listening":
        meta.append(pill("文字仿真", bg="#EEF4F3", fg=SUCCESS, size=9))
    else:
        meta.append(
            ft.Text(
                question.get("section", ""),
                size=9.5,
                color=FAINT,
                no_wrap=True,
            )
        )
    return frosted_panel(
        ft.Column(
            [
                ft.Row(meta, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(
                    content=selectable_text(
                        question.get("material", ""),
                        size=13 if compact else 13.5,
                        on_select=on_select,
                    ),
                    padding=ft.Padding.only(top=2),
                ),
            ],
            spacing=9,
        ),
        padding=16,
        radius=16,
        fill=0.50,
        border_color="#E4EDF5",
    )


def question_meta_line(
    question: dict[str, Any],
    number: int,
    total: int,
    *,
    marked: bool = False,
) -> ft.Control:
    type_label = (
        "多选题 · 可选多个"
        if question.get("type") == "multiple"
        else "单选题"
    )
    controls: list[ft.Control] = [
        pill(
            f"{section_cn(question.get('category', ''))} · {question.get('section', '')}",
            bg=TEAL_LIGHT,
            fg=TEAL_DARK,
            size=10,
        ),
        pill(type_label, bg=SKY, fg=INDIGO, size=10),
        ft.Container(expand=True),
        ft.Text(
            f"{number:02d} / {total}",
            size=10.5,
            color=FAINT,
            no_wrap=True,
        ),
    ]
    if marked:
        controls.append(ft.Icon(ft.Icons.BOOKMARK_ROUNDED, size=14, color=WARNING))
    return ft.Row(
        controls,
        spacing=7,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def question_prompt(question: dict[str, Any]) -> ft.Control:
    return ft.Text(
        question.get("question", ""),
        size=17,
        weight=ft.FontWeight.W_700,
        color=INK,
        style=ft.TextStyle(height=1.5),
        selectable=True,
    )


def section_strip(question: dict[str, Any]) -> ft.Control:
    return ft.Row(
        [
            ft.Column(
                [
                    ft.Text(
                        section_name(question.get("category", "")),
                        size=9.5,
                        weight=ft.FontWeight.W_700,
                        color=TEAL_DARK,
                        no_wrap=True,
                    ),
                    ft.Text(
                        section_cn(question.get("category", "")),
                        size=10,
                        color=FAINT,
                        no_wrap=True,
                    ),
                ],
                spacing=0,
            ),
            ft.Container(expand=True),
            ft.Text(
                CATEGORY_LABELS.get(question.get("category", ""), ""),
                size=10,
                color=FAINT,
                no_wrap=True,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def explanation_block(
    question: dict[str, Any],
    user_answer: list[str],
    *,
    is_ok: bool,
) -> ft.Control:
    if is_ok:
        header_bg = SUCCESS_BG
        header_fg = SUCCESS
        header_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
        header_text = "回答正确"
    else:
        header_bg = DANGER_BG
        header_fg = DANGER
        header_icon = ft.Icons.CANCEL_ROUNDED
        header_text = "回答错误 · 已自动收录错题本"
    return ft.Column(
        [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(header_icon, size=18, color=header_fg),
                        ft.Text(header_text, size=12.5, weight=ft.FontWeight.W_700, color=header_fg),
                        ft.Container(expand=True),
                        ft.Text(
                            f"正确答案 {answer_text(question.get('answers'))}",
                            size=10.5,
                            color=header_fg,
                            no_wrap=True,
                        ),
                    ],
                    spacing=7,
                ),
                padding=ft.Padding.symmetric(horizontal=13, vertical=10),
                border_radius=12,
                bgcolor=header_bg,
            ),
            frosted_panel(
                ft.Column(
                    [
                        ft.Row(
                            [
                                icon_box(
                                    ft.Icons.LIGHTBULB_ROUNDED,
                                    color=WARNING,
                                    bg="#F8ECD9",
                                    size=30,
                                    icon_size=15,
                                    radius=9,
                                ),
                                ft.Text("详细解析", size=11.5, weight=ft.FontWeight.W_700, color=INK),
                                ft.Container(expand=True),
                                ft.Text(
                                    f"你的答案 {answer_text(user_answer)}",
                                    size=9.5,
                                    color=FAINT,
                                    no_wrap=True,
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            question.get("explanation", ""),
                            size=12.5,
                            color=INK_SOFT,
                            selectable=True,
                            style=ft.TextStyle(height=1.75),
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
                fill=0.52,
            ),
        ],
        spacing=10,
    )
