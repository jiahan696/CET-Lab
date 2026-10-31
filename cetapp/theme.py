"""Shared visual language: liquid-glass surfaces, restrained color, soft depth.

All controls are laid out with Flet's responsive primitives. Cards use
translucent fills over a blurred, low-saturation gradient so the glass effect
survives resizing and both desktop and mobile form factors.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

# ---------------------------------------------------------------- palette
INK = "#17324D"
INK_SOFT = "#344E68"
MUTED = "#6C8095"
FAINT = "#8EA0B3"
TEAL = "#317D84"
TEAL_DARK = "#22636C"
TEAL_LIGHT = "#DCEDEB"
INDIGO = "#6474C8"
INDIGO_LIGHT = "#E7EAF8"
MINT = "#DDEEE8"
SKY = "#E4EDF8"
SAND = "#F3E9D8"
BLUSH = "#F3E1DF"
SUCCESS = "#2F8B6D"
SUCCESS_BG = "#E0F2EA"
DANGER = "#C15B6B"
DANGER_BG = "#F8E4E7"
WARNING = "#B47725"
WARNING_BG = "#F8ECD9"
LINE = "#D8E4EE"
LINE_SOFT = "#E7EFF6"
WHITE = "#FFFFFF"


def alpha(color: str, value: float) -> str:
    """Alpha over a hex color, clamped for Flet's ARGB parser."""
    value = max(0.0, min(1.0, value))
    return ft.Colors.with_opacity(value, color)


def soft_shadow(spread: float = 0, blur: float = 34, dy: float = 16, opacity: float = 0.10) -> ft.BoxShadow:
    return ft.BoxShadow(
        spread_radius=spread,
        blur_radius=blur,
        color=ft.Colors.with_opacity(opacity, "#16324D"),
        offset=ft.Offset(0, dy),
    )


# ---------------------------------------------------------------- surfaces
def glass_card(
    content: ft.Control,
    *,
    padding: int | float | ft.Padding = 24,
    radius: int = 24,
    fill: float = 0.70,
    border_color: str | None = None,
    shadow: bool = True,
    width: int | float | None = None,
    height: int | float | None = None,
    expand: bool | int | None = None,
    **kwargs: Any,
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        width=width,
        height=height,
        expand=expand,
        bgcolor=ft.Colors.with_opacity(fill, WHITE),
        border=ft.Border.all(
            1, border_color or ft.Colors.with_opacity(0.70, "#FFFFFF")
        ),
        border_radius=radius,
        shadow=soft_shadow() if shadow else None,
        **kwargs,
    )


def frosted_panel(
    content: ft.Control,
    *,
    padding: int | float | ft.Padding = 16,
    radius: int = 18,
    fill: float = 0.46,
    border_color: str = "#E3ECF4",
    **kwargs: Any,
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=ft.Colors.with_opacity(fill, WHITE),
        border=ft.Border.all(1, border_color),
        border_radius=radius,
        **kwargs,
    )


def background() -> ft.Stack:
    blob = lambda color, size, left=None, top=None, right=None, bottom=None: ft.Container(
        width=size,
        height=size,
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        border_radius=size / 2,
        gradient=ft.RadialGradient(
            colors=[ft.Colors.with_opacity(0.62, color), ft.Colors.with_opacity(0.0, color)],
            radius=0.78,
        ),
        blur=ft.Blur(46, 46),
    )
    return ft.Stack(
        expand=True,
        controls=[
            ft.Container(
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=["#F9FBFF", "#EFF4FA", "#F7FAFD", "#EEF3F8"],
                    stops=[0.0, 0.36, 0.72, 1.0],
                ),
            ),
            blob("#A7D4D8", 560, left=-210, top=-220),
            blob("#C9D3F5", 600, right=-220, top=-180),
            blob("#F1D9D3", 480, right=-140, bottom=-220),
            blob("#CFE4D9", 420, left=-150, bottom=-190),
            ft.Container(
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.06, "#FFFFFF"),
            ),
        ],
    )


# ---------------------------------------------------------------- type
def eyebrow(text: str, color: str = TEAL) -> ft.Text:
    return ft.Text(
        text,
        size=11,
        weight=ft.FontWeight.W_700,
        color=color,
        no_wrap=True,
    )


def heading(text: str, size: int = 30, color: str = INK) -> ft.Text:
    return ft.Text(
        text,
        size=size,
        weight=ft.FontWeight.W_700,
        color=color,
        style=ft.TextStyle(height=1.18),
    )


def body(text: str, size: int = 14, color: str = MUTED, **kwargs: Any) -> ft.Text:
    return ft.Text(text, size=size, color=color, style=ft.TextStyle(height=1.55), **kwargs)


# ---------------------------------------------------------------- controls
def pill(
    text: str,
    *,
    icon: ft.IconData | None = None,
    bg: str = TEAL_LIGHT,
    fg: str = TEAL_DARK,
    size: int = 12,
    padding: int | float | ft.Padding = 10,
    border: str | None = None,
) -> ft.Container:
    controls: list[ft.Control] = []
    if icon:
        controls.append(ft.Icon(icon, size=14, color=fg))
    controls.append(
        ft.Text(text, size=size, color=fg, weight=ft.FontWeight.W_600, no_wrap=True)
    )
    return ft.Container(
        content=ft.Row(controls, spacing=6, tight=True, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=padding, vertical=6),
        bgcolor=bg,
        border=ft.Border.all(1, border) if border else None,
        border_radius=999,
    )


def icon_box(
    icon: ft.IconData,
    *,
    color: str = TEAL,
    bg: str = TEAL_LIGHT,
    size: int = 44,
    icon_size: int = 21,
    radius: int = 14,
) -> ft.Container:
    return ft.Container(
        width=size,
        height=size,
        border_radius=radius,
        bgcolor=bg,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.55, "#FFFFFF")),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(icon, size=icon_size, color=color),
    )


def action_button(
    label: str,
    *,
    on_click: Callable[[], Any] | None = None,
    icon: ft.IconData | None = None,
    variant: str = "primary",
    height: int = 46,
    expand: bool = False,
    width: int | float | None = None,
    icon_size: int = 17,
    font_size: int = 14,
) -> ft.Container:
    if variant == "primary":
        bg = None
        gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, 0),
            end=ft.Alignment(1, 1),
            colors=[TEAL, "#2A6C7B"],
        )
        fg = WHITE
        border = ft.Border.all(1, ft.Colors.with_opacity(0.32, "#FFFFFF"))
        shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=18,
            color=ft.Colors.with_opacity(0.24, TEAL),
            offset=ft.Offset(0, 8),
        )
    elif variant == "secondary":
        bg = ft.Colors.with_opacity(0.62, WHITE)
        gradient = None
        fg = INK
        border = ft.Border.all(1, "#D9E6F0")
        shadow = soft_shadow(blur=18, dy=8, opacity=0.06)
    elif variant == "ghost":
        bg = None
        gradient = None
        fg = TEAL_DARK
        border = None
        shadow = None
    else:  # danger
        bg = DANGER_BG
        gradient = None
        fg = DANGER
        border = ft.Border.all(1, "#F0C9CF")
        shadow = None
    controls: list[ft.Control] = []
    if icon:
        controls.append(ft.Icon(icon, size=icon_size, color=fg))
    controls.append(
        ft.Text(label, size=font_size, color=fg, weight=ft.FontWeight.W_600, no_wrap=True)
    )
    clickable = on_click is not None
    return ft.Container(
        content=ft.Row(
            controls,
            spacing=7,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        height=height,
        width=width,
        expand=expand or None,
        padding=ft.Padding.symmetric(horizontal=18),
        bgcolor=bg,
        gradient=gradient,
        border=border,
        border_radius=14,
        shadow=shadow,
        ink=clickable and bg is not None,
        on_click=(lambda _e: on_click()) if clickable else None,
        opacity=1.0,
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
    )


def text_action(
    label: str,
    on_click: Callable[[], Any],
    *,
    icon: ft.IconData | None = None,
    color: str = TEAL_DARK,
    size: int = 13,
) -> ft.Container:
    controls: list[ft.Control] = []
    if icon:
        controls.append(ft.Icon(icon, size=15, color=color))
    controls.append(ft.Text(label, size=size, color=color, weight=ft.FontWeight.W_600))
    return ft.Container(
        content=ft.Row(controls, spacing=5, tight=True),
        padding=ft.Padding.symmetric(horizontal=4, vertical=4),
        on_click=lambda _e: on_click(),
    )


def nav_item(
    label: str,
    icon: ft.IconData,
    active: bool,
    on_click: Callable[[], Any],
    *,
    compact: bool = False,
) -> ft.Container:
    fg = TEAL_DARK if active else MUTED
    content: ft.Control
    if compact:
        content = ft.Icon(icon, size=17, color=fg)
    else:
        content = ft.Row(
            [
                ft.Icon(icon, size=16, color=fg),
                ft.Text(
                    label,
                    size=12.5,
                    color=fg,
                    weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_500,
                    no_wrap=True,
                ),
            ],
            spacing=6,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    return ft.Container(
        content=content,
        padding=ft.Padding.symmetric(horizontal=9 if compact else 12, vertical=9),
        bgcolor=ft.Colors.with_opacity(0.64, WHITE) if active else None,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.8, WHITE)) if active else None,
        border_radius=999,
        on_click=lambda _e: on_click(),
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        tooltip=label,
    )


def divider(color: str = LINE_SOFT) -> ft.Container:
    return ft.Container(height=1, bgcolor=color, border_radius=1)


def progress_track(
    value: float,
    *,
    height: int = 7,
    color: str = TEAL,
    bg: str = "#E4EDF3",
) -> ft.ProgressBar:
    return ft.ProgressBar(
        value=max(0.0, min(1.0, value)),
        height=height,
        bar_height=height,
        color=color,
        bgcolor=bg,
        border_radius=999,
    )


def empty_state(
    title: str,
    subtitle: str,
    *,
    icon: ft.IconData = ft.Icons.INBOX_ROUNDED,
    action: ft.Control | None = None,
) -> ft.Container:
    children: list[ft.Control] = [
        icon_box(icon, size=52, icon_size=25, bg=SKY, color=INDIGO),
        ft.Text(title, size=17, weight=ft.FontWeight.W_700, color=INK, text_align=ft.TextAlign.CENTER),
        body(subtitle, size=13, text_align=ft.TextAlign.CENTER),
    ]
    if action:
        children.append(ft.Container(height=4))
        children.append(action)
    return ft.Container(
        content=ft.Column(children, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.Alignment(0, 0),
        padding=ft.Padding.symmetric(vertical=44, horizontal=20),
    )


def selectable_text(
    value: str,
    *,
    size: float = 13.5,
    color: str = INK_SOFT,
    line_height: float = 1.72,
    on_select=None,
) -> ft.TextField:
    """A read-only, borderless TextField used for selectable passages.

    Flet's Text control reports the whole paragraph as ``selected_text``;
    TextField reports the actual dragged substring, which is what 划词翻译 needs.
    """
    return ft.TextField(
        value=value,
        multiline=True,
        read_only=True,
        border=ft.InputBorder.NONE,
        filled=False,
        bgcolor=ft.Colors.TRANSPARENT,
        content_padding=ft.Padding.all(0),
        text_size=size,
        color=color,
        text_style=ft.TextStyle(height=line_height),
        show_cursor=False,
        on_selection_change=(
            (lambda e: on_select(e.selected_text)) if on_select else None
        ),
    )
