from __future__ import annotations

import asyncio
import os
import traceback
from typing import Any

import flet as ft

from . import APP_TITLE, APP_VERSION
from .ai_agent import AIAgentClient, AIAgentConfig
from .paperlib import PaperLibrary, paper_questions
from .questions import CATEGORY_LABELS, load_question_bank
from .scoring import score_line
from .store import Store
from .theme import (
    DANGER,
    DANGER_BG,
    FAINT,
    INDIGO,
    INDIGO_LIGHT,
    INK,
    INK_SOFT,
    LINE,
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
    background,
    body,
    divider,
    eyebrow,
    glass_card,
    heading,
    icon_box,
    nav_item,
    pill,
)
from .utils import fmt_score, full_date, percent


class CETApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.questions = load_question_bank()
        self.question_by_id = {q["id"]: q for q in self.questions}
        self.store = Store()
        self.library = PaperLibrary(self.store.path.parent)
        self.ai = AIAgentClient(self.store.path.parent / "ai_config.json")
        self.route = "home"
        self._selection_seq = 0
        self.file_picker = ft.FilePicker()
        self.current_view: Any = None
        self.last_result: dict[str, Any] | None = None
        self._compact_nav = False
        self.topbar_host: ft.Container | None = None
        self._configure_page()
        self.root = ft.Stack(expand=True, controls=[])
        self.page.add(self.root)
        self.navigate("home")
        self.page.run_task(self._style_window)
        self._handle_expired_session()
        self.page.run_task(self._watchdog_loop)

    async def _style_window(self) -> None:
        """Make Windows caption buttons legible on the light glass theme."""
        if os.name != "nt":
            return
        try:
            import ctypes

            await asyncio.sleep(1.2)
            hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
            if not hwnd:
                await asyncio.sleep(1.0)
                hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
            if not hwnd:
                return
            enabled = ctypes.c_int(1)
            # DWMWA_USE_IMMERSIVE_DARK_MODE: white caption glyphs on a dark frame.
            for attribute in (20, 19):
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(enabled), ctypes.sizeof(enabled)
                )
                if result == 0:
                    break
        except Exception:
            pass

    async def _watchdog_loop(self) -> None:
        """Global guard: exams expire even when the user is not on the exam page."""
        await asyncio.sleep(2.0)
        while True:
            try:
                session = self.store.active_exam
                if session and self.route != "exam":
                    from .exam_service import finalize_exam, finalize_paper_exam
                    from .scoring import remaining_seconds

                    if remaining_seconds(session) <= 0:
                        if session.get("paper_id"):
                            paper = self.library.get(session["paper_id"])
                            if not paper:
                                await asyncio.sleep(3.0)
                                continue
                            record = finalize_paper_exam(
                                self.store,
                                paper,
                                session,
                                completed_by="timeout",
                            )
                        else:
                            record = finalize_exam(
                                self.store,
                                self.questions,
                                session,
                                completed_by="timeout",
                            )
                        self.last_result = record
                        try:
                            self.page.pop_dialog()
                        except Exception:
                            pass
                        self.navigate("result", record=record)
                        self.notify("考试时间到，系统已自动交卷。", "warning")
            except Exception:
                traceback.print_exc()
            await asyncio.sleep(3.0)

    def _handle_expired_session(self) -> None:
        session = self.store.active_exam
        if not session:
            return
        from .exam_service import finalize_exam, finalize_paper_exam
        from .scoring import remaining_seconds

        if remaining_seconds(session) > 0:
            return
        try:
            if session.get("paper_id"):
                paper = self.library.get(session["paper_id"])
                if not paper:
                    return
                record = finalize_paper_exam(
                    self.store,
                    paper,
                    session,
                    completed_by="timeout",
                )
            else:
                record = finalize_exam(
                    self.store,
                    self.questions,
                    session,
                    completed_by="timeout",
                )
            self.last_result = record
            self.navigate("result", record=record)
            self.notify("上次考试已超时，系统已自动交卷。", "warning")
        except Exception:
            traceback.print_exc()

    # ------------------------------------------------------------------ page
    def _configure_page(self) -> None:
        self.page.title = APP_TITLE
        self.page.bgcolor = "#EFF4FA"
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.theme = ft.Theme(
            use_material3=True,
            color_scheme_seed=TEAL,
            scaffold_bgcolor="#EFF4FA",
        )
        self.page.window.width = 1200
        self.page.window.height = 820
        self.page.window.min_width = 380
        self.page.window.min_height = 620
        self.page.window.bgcolor = "#EFF4FA"
        self.page.on_close = self._on_close
        self.page.on_error = self._on_error
        self.page.on_resize = self._on_resize
        self.page.services.append(self.file_picker)

    # --------------------------------------------------------------- routing
    def navigate(self, route: str, **kwargs: Any) -> None:
        if self.current_view is not None and hasattr(self.current_view, "on_leave"):
            try:
                self.current_view.on_leave()
            except Exception:
                traceback.print_exc()
        self.route = route
        try:
            if route == "home":
                from .views.dashboard import DashboardView

                view = DashboardView(self)
            elif route == "exam":
                from .views.paper_exam import PaperExamView

                view = PaperExamView(self)
            elif route == "practice":
                from .views.practice import PracticeView

                view = PracticeView(self, category=kwargs.get("category"))
            elif route == "wrongbook":
                from .views.wrongbook import WrongbookView

                view = WrongbookView(self)
            elif route == "wordbook":
                from .views.wordbook import WordbookView

                view = WordbookView(self)
            elif route == "import":
                from .views.import_paper import ImportPaperView

                view = ImportPaperView(self)
            elif route == "history":
                from .views.history import HistoryView

                view = HistoryView(self)
            elif route == "result":
                from .views.result import ResultView

                record = kwargs.get("record") or self.last_result
                if not record:
                    view = DashboardView(self)
                    self.route = "home"
                else:
                    self.last_result = record
                    view = ResultView(self, record)
            else:
                from .views.dashboard import DashboardView

                view = DashboardView(self)
                self.route = "home"
        except Exception:
            traceback.print_exc()
            self._fatal_view()
            return
        self.current_view = view
        self.render()

    def render(self) -> None:
        if self.current_view is None:
            return
        control = self.current_view.build()
        full_screen = bool(getattr(self.current_view, "full_screen", False))
        try:
            self._compact_nav = float(self.page.width or 0) < 760
        except Exception:
            self._compact_nav = False
        if full_screen:
            self.topbar_host = None
            shell: ft.Control = ft.SafeArea(content=control, expand=True)
        else:
            body_column = ft.Column(
                [control],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                spacing=0,
            )
            self.topbar_host = ft.Container(content=self._topbar())
            shell = ft.SafeArea(
                content=ft.Container(
                    content=ft.Column(
                        [
                            self.topbar_host,
                            ft.Container(
                                content=body_column,
                                expand=True,
                                padding=ft.Padding.only(top=14, bottom=18),
                            ),
                        ],
                        expand=True,
                        spacing=0,
                    ),
                    padding=ft.Padding.symmetric(horizontal=18, vertical=12),
                    expand=True,
                ),
                expand=True,
                minimum_padding=0,
            )
        self.root.controls = [background(), shell]
        self.page.update()

    def _on_resize(self, _e=None) -> None:
        try:
            width = float(self.page.width or 0)
        except Exception:
            return
        compact = width < 760
        if self.topbar_host is not None and compact != self._compact_nav:
            self._compact_nav = compact
            try:
                self.topbar_host.content = self._topbar()
                self.page.update()
            except Exception:
                traceback.print_exc()
        if self.current_view is not None and hasattr(self.current_view, "on_window_resize"):
            try:
                self.current_view.on_window_resize(width)
            except Exception:
                traceback.print_exc()

    def library_questions(self, paper: dict[str, Any]) -> list[dict[str, Any]]:
        return paper_questions(paper)

    def find_question(self, qid: str) -> dict[str, Any] | None:
        for q in self.questions:
            if q["id"] == qid:
                return q
        return self.library.get_by_question_id(qid)

    def rerender(self) -> None:
        """Rebuild the current view after external state changes."""
        self.render()

    # ----------------------------------------------------------------- topbar
    def _topbar(self) -> ft.Control:
        active = self.route
        compact = self._compact_nav
        brand_items: list[ft.Control] = [
            ft.Container(
                width=32,
                height=32,
                border_radius=10,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=[TEAL, "#5C6BBE"],
                ),
                alignment=ft.Alignment(0, 0),
                content=ft.Text("C", size=16, weight=ft.FontWeight.W_800, color=WHITE),
                shadow=ft.BoxShadow(
                    blur_radius=14,
                    color=ft.Colors.with_opacity(0.24, TEAL),
                    offset=ft.Offset(0, 5),
                ),
            )
        ]
        if not compact:
            brand_items.append(
                ft.Column(
                    [
                        ft.Text("CET·LAB", size=12.5, weight=ft.FontWeight.W_800, color=INK, no_wrap=True),
                        ft.Text("GLASS EXAM", size=8, color=FAINT, no_wrap=True),
                    ],
                    spacing=0,
                )
            )
        brand = ft.Container(
            content=ft.Row(
                brand_items,
                spacing=8,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=8 if compact else 8, vertical=5),
            border_radius=14,
            on_click=lambda _e: self.navigate("home"),
            tooltip="返回首页",
        )
        nav = ft.Row(
            [
                nav_item("模考", ft.Icons.TIMER_ROUNDED, active == "exam", lambda: self.navigate("exam"), compact=compact),
                nav_item("刷题", ft.Icons.EDIT_NOTE_ROUNDED, active == "practice", lambda: self.navigate("practice"), compact=compact),
                nav_item("单词", ft.Icons.MENU_BOOK_ROUNDED, active == "wordbook", lambda: self.navigate("wordbook"), compact=compact),
                nav_item("错题", ft.Icons.BOOKMARK_ROUNDED, active == "wrongbook", lambda: self.navigate("wrongbook"), compact=compact),
                nav_item("成绩", ft.Icons.INSIGHTS_ROUNDED, active == "history", lambda: self.navigate("history"), compact=compact),
                nav_item("AI", ft.Icons.AUTO_AWESOME_ROUNDED, False, self.show_ai_settings, compact=compact),
            ],
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        status_items: list[ft.Control] = [
            ft.Container(width=6, height=6, border_radius=3, bgcolor=SUCCESS)
        ]
        if not compact:
            status_items.append(ft.Text("本地保存", size=10, color=MUTED, no_wrap=True))
        return glass_card(
            ft.Row(
                [
                    brand,
                    ft.Container(
                        content=nav,
                        expand=True,
                        alignment=ft.Alignment(1, 0),
                    ),
                    ft.Container(
                        content=ft.Row(
                            status_items,
                            spacing=5,
                            tight=True,
                        ),
                        padding=ft.Padding.only(left=6, right=3),
                        tooltip="所有数据保存在本地 JSON",
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=ft.Padding.symmetric(horizontal=9, vertical=7),
            radius=20,
            fill=0.58,
        )

    # -------------------------------------------------------------- feedback
    def notify(self, message: str, tone: str = "info") -> None:
        tones = {
            "info": (ft.Icons.INFO_OUTLINE_ROUNDED, "#EAF1F8", INK),
            "success": (ft.Icons.CHECK_CIRCLE_ROUNDED, SUCCESS_BG, SUCCESS),
            "warning": (ft.Icons.LIGHTBULB_ROUNDED, "#F8ECD9", WARNING),
            "error": (ft.Icons.ERROR_OUTLINE_ROUNDED, DANGER_BG, DANGER),
        }
        icon, bg, fg = tones.get(tone, tones["info"])
        snack = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(icon, size=18, color=fg),
                    ft.Text(message, size=12.5, color=INK, weight=ft.FontWeight.W_500),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.with_opacity(0.98, bg),
            duration=2600,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin.only(left=18, right=18, bottom=16),
            shape=ft.RoundedRectangleBorder(radius=15),
            show_close_icon=False,
        )
        self.page.show_dialog(snack)

    def _dialog_width(self, preferred: int = 420) -> int:
        try:
            return max(280, min(preferred, int(self.page.width) - 90))
        except Exception:
            return preferred

    def confirm(
        self,
        title: str,
        message: str,
        *,
        confirm_label: str = "确认",
        cancel_label: str = "取消",
        danger: bool = False,
        on_confirm=None,
    ) -> None:
        def close() -> None:
            self.page.pop_dialog()

        def accept(_e=None) -> None:
            self.page.pop_dialog()
            if on_confirm:
                on_confirm()

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.with_opacity(0.97, WHITE),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Column(
                [
                    icon_box(
                        ft.Icons.ERROR_OUTLINE_ROUNDED if danger else ft.Icons.HELP_OUTLINE_ROUNDED,
                        color=DANGER if danger else TEAL,
                        bg=DANGER_BG if danger else TEAL_LIGHT,
                        size=42,
                        icon_size=21,
                        radius=13,
                    ),
                    ft.Text(title, size=19, weight=ft.FontWeight.W_700, color=INK),
                ],
                spacing=10,
            ),
            content=ft.Container(
                width=self._dialog_width(390),
                content=ft.Text(message, size=13, color=MUTED, style=ft.TextStyle(height=1.6)),
            ),
            actions=[
                action_button(
                    cancel_label,
                    variant="secondary",
                    height=40,
                    font_size=12.5,
                    on_click=close,
                ),
                action_button(
                    confirm_label,
                    variant="danger" if danger else "primary",
                    height=40,
                    font_size=12.5,
                    on_click=accept,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def show_history_detail(self, record: dict[str, Any]) -> None:
        sections = record.get("sections", {}) or {}
        rows = []
        meta = []
        if "writing" in sections:
            meta.append(("writing", "写作"))
        meta.extend([("listening", "听力"), ("reading", "阅读"), ("translation", "翻译")])
        for category, label in meta:
            rows.append(
                ft.Row(
                    [
                        ft.Text(label, size=12, color=MUTED),
                        ft.Container(expand=True),
                        ft.Text(
                            fmt_score(sections.get(category, 0)),
                            size=14,
                            weight=ft.FontWeight.W_700,
                            color=INK,
                        ),
                    ]
                )
            )
        content = ft.Container(
            width=self._dialog_width(430),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("总分", size=10.5, color=FAINT),
                                    ft.Text(fmt_score(record.get("score", 0)), size=34, weight=ft.FontWeight.W_800, color=TEAL_DARK),
                                ],
                                spacing=0,
                            ),
                            ft.Container(expand=True),
                            pill(record.get("level", "CET-4"), bg=SKY, fg=INK_SOFT),
                            pill("自动交卷" if record.get("completed_by") == "timeout" else "手动交卷", bg=TEAL_LIGHT, fg=TEAL_DARK, size=10),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        record.get("paper_title") or full_date(record.get("completed_at", "")),
                        size=11,
                        color=FAINT,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    divider(),
                    ft.Row(
                        [
                            ft.Column([ft.Text("正确率", size=10.5, color=FAINT), ft.Text(percent(record.get("accuracy", 0)), size=16, weight=ft.FontWeight.W_700, color=INK)], spacing=1, expand=True),
                            ft.Column([ft.Text("答对", size=10.5, color=FAINT), ft.Text(f"{record.get('correct', 0)} / {record.get('total', 45)}", size=16, weight=ft.FontWeight.W_700, color=INK)], spacing=1, expand=True),
                            ft.Column([ft.Text("用时", size=10.5, color=FAINT), ft.Text(f"{int(record.get('duration_sec', 0)) // 60} 分钟", size=16, weight=ft.FontWeight.W_700, color=INK)], spacing=1, expand=True),
                        ],
                        spacing=10,
                    ),
                    divider(),
                    ft.Column(rows, spacing=8),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.BOOKMARK_ROUNDED, size=16, color=DANGER),
                                ft.Text("本次错题已自动加入错题本", size=11.5, color=DANGER),
                            ],
                            spacing=7,
                        ),
                        padding=11,
                        border_radius=12,
                        bgcolor=DANGER_BG,
                    ),
                ],
                spacing=12,
            ),
        )
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.with_opacity(0.97, WHITE),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Text("成绩详情", size=19, weight=ft.FontWeight.W_700, color=INK),
            content=content,
            actions=[
                action_button(
                    "关闭",
                    variant="secondary",
                    height=40,
                    font_size=12.5,
                    on_click=lambda: self.page.pop_dialog(),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    # ---------------------------------------------------------- AI features
    def show_ai_settings(self) -> None:
        cfg = self.ai.load_config()
        base = ft.TextField(
            label="Base URL",
            value=cfg.base_url,
            hint_text="https://api.deepseek.com/v1",
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.45, WHITE),
            border_color="#D8E4EE",
            focused_border_color=TEAL,
            color=INK,
            text_size=12,
        )
        model = ft.TextField(
            label="模型",
            value=cfg.model,
            hint_text="deepseek-flash",
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.45, WHITE),
            border_color="#D8E4EE",
            focused_border_color=TEAL,
            color=INK,
            text_size=12,
        )
        api_key = ft.TextField(
            label="API Key",
            value=cfg.api_key,
            password=True,
            can_reveal_password=True,
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.45, WHITE),
            border_color="#D8E4EE",
            focused_border_color=TEAL,
            color=INK,
            text_size=12,
        )
        enabled = ft.Switch(value=cfg.enabled, active_color=TEAL, label="启用 AI")

        def save() -> None:
            new_cfg = AIAgentConfig(
                enabled=bool(enabled.value),
                base_url=(base.value or "").strip() or "https://api.deepseek.com/v1",
                api_key=(api_key.value or "").strip(),
                model=(model.value or "").strip() or "deepseek-flash",
                timeout=cfg.timeout,
                temperature=cfg.temperature,
            )
            self.ai.save_config(new_cfg)
            self.page.pop_dialog()
            state = "已启用" if new_cfg.configured else "已保存，但尚未启用或未填写 Key"
            self.notify(f"AI 配置{state}。", "success" if new_cfg.configured else "warning")

        def test() -> None:
            async def run_test() -> None:
                try:
                    text = await self.ai.chat(
                        [{"role": "user", "content": "只回复：AI OK"}],
                        max_tokens=1200,
                    )
                    self.notify("AI 连接成功：" + text[:40], "success")
                except Exception as exc:
                    self.notify(f"AI 连接失败：{exc}", "error")

            self.page.run_task(run_test)

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.with_opacity(0.98, WHITE),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Row(
                [
                    icon_box(ft.Icons.AUTO_AWESOME_ROUNDED, color=INDIGO, bg=INDIGO_LIGHT, size=38, icon_size=18, radius=12),
                    ft.Text("AI 设置", size=19, weight=ft.FontWeight.W_700, color=INK),
                ],
                spacing=10,
            ),
            content=ft.Container(
                width=self._dialog_width(520),
                content=ft.Column(
                    [
                        body(
                            "划词翻译、写作/翻译评分、PDF 试卷导入都使用同一个 OpenAI-compatible 接口。"
                            "API Key 仅保存在本机。",
                            size=11.5,
                        ),
                        base,
                        model,
                        api_key,
                        ft.Row([enabled, ft.Container(expand=True)], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                action_button("测试连接", variant="secondary", height=38, font_size=11.5, on_click=test),
                action_button("保存", height=38, font_size=11.5, on_click=save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def translate_selection(self, text: str, *, context: str = "", source: str = "") -> None:
        text = (text or "").strip()
        if not text or len(text) > 500:
            return
        self._selection_seq += 1
        seq = self._selection_seq
        self.page.run_task(self._translate_selection_task, text, context, source, seq)

    async def _translate_selection_task(self, text: str, context: str, source: str, seq: int) -> None:
        await asyncio.sleep(0.65)
        if seq != self._selection_seq:
            return
        if not self.ai.available:
            self.notify("AI 尚未配置，无法划词翻译。", "warning")
            self.show_ai_settings()
            return
        self.notify("AI 正在翻译选中的内容…", "info")
        try:
            data = await self.ai.translate_selection(text, context=context)
        except Exception as exc:
            self.notify(f"翻译失败：{exc}", "error")
            return
        if seq != self._selection_seq:
            return
        translation = str(data.get("translation") or "").strip()
        term = str(data.get("term") or text).strip()
        phonetic = str(data.get("phonetic") or "").strip()
        pos = str(data.get("part_of_speech") or "").strip()
        example = str(data.get("example") or "").strip()

        def add_word() -> None:
            self.store.add_word(
                term,
                translation,
                context=context,
                source=source,
                phonetic=phonetic,
                part_of_speech=pos,
                example=example,
            )
            try:
                self.page.pop_dialog()
            except Exception:
                pass
            self.notify(f"已加入单词本：{term}", "success")

        sheet = ft.BottomSheet(
            show_drag_handle=True,
            dismissible=True,
            bgcolor=ft.Colors.with_opacity(0.98, WHITE),
            content=ft.Container(
                padding=ft.Padding.only(left=22, right=22, top=6, bottom=22),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                icon_box(ft.Icons.TRANSLATE_ROUNDED, color=TEAL, bg=TEAL_LIGHT, size=36, icon_size=17, radius=11),
                                ft.Column(
                                    [
                                        ft.Text(term, size=18, weight=ft.FontWeight.W_700, color=INK),
                                        ft.Text(
                                            " ".join(x for x in [pos, phonetic] if x),
                                            size=10.5,
                                            color=FAINT,
                                        ),
                                    ],
                                    spacing=0,
                                    expand=True,
                                ),
                                action_button("加入单词本", icon=ft.Icons.BOOKMARK_ADD_ROUNDED, height=38, font_size=11.5, on_click=add_word),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Text(translation, size=14, color=INK, selectable=True, style=ft.TextStyle(height=1.65)),
                            padding=14,
                            border_radius=14,
                            bgcolor=ft.Colors.with_opacity(0.5, TEAL_LIGHT),
                        ),
                        ft.Text(f"原文：{text}", size=11, color=MUTED, selectable=True),
                        *([ft.Text(f"例句：{example}", size=11, color=INK_SOFT, selectable=True)] if example else []),
                        ft.Row(
                            [
                                ft.Text("由 AI 生成 · 可加入单词本复习", size=9.5, color=FAINT, expand=True),
                                action_button("关闭", variant="secondary", height=34, font_size=11, on_click=lambda: self.page.pop_dialog()),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=11,
                ),
            ),
        )
        self.page.show_dialog(sheet)

    # --------------------------------------------------------------- shutdown
    def _on_close(self, _e=None) -> None:
        try:
            if self.current_view is not None and hasattr(self.current_view, "on_app_close"):
                self.current_view.on_app_close()
            self.store.save()
        except Exception:
            traceback.print_exc()

    def _on_error(self, e=None) -> None:
        error_log = self.store.path.parent / "ui_error.log"
        with open(error_log, "a", encoding="utf-8") as fh:
            fh.write("---- on_error ----\n")
            fh.write(repr(e) + "\n")
            fh.write(str(getattr(e, "data", "")) + "\n")
            fh.write(str(getattr(e, "error", "")) + "\n")
            fh.write(traceback.format_exc() + "\n")
        traceback.print_exc()

    def _fatal_view(self) -> None:
        control = glass_card(
            ft.Column(
                [
                    heading("页面加载失败", 24),
                    body("应用遇到错误，但本地数据不会丢失。请返回首页重试。", 13),
                    action_button("返回首页", on_click=lambda: self.navigate("home")),
                ],
                spacing=14,
            ),
            padding=28,
        )
        self.current_view = None
        self.root.controls = [
            background(),
            ft.SafeArea(
                content=ft.Container(content=control, padding=40, expand=True),
                expand=True,
            ),
        ]
        self.page.update()


def main(page: ft.Page) -> None:
    CETApp(page)
