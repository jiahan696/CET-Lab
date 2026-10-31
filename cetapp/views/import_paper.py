from __future__ import annotations

import asyncio
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from ..pdf_import import build_imported_paper
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
    text_action,
)
from ..utils import now_iso

if TYPE_CHECKING:
    from ..app import CETApp


class ImportPaperView:
    full_screen = False

    def __init__(self, app: "CETApp") -> None:
        self.app = app
        self.level = "CET-4"
        self.question_pdf: Path | None = None
        self.answer_pdf: Path | None = None
        self.audio: Path | None = None
        self.name_value = ""
        self.minutes_value = "125"
        self.use_vision_value = True
        self.busy = False

    def build(self) -> ft.Control:
        self.name_field = ft.TextField(
            label="试卷名称",
            value=self.name_value,
            hint_text="例如：我的四级模考卷",
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.46, WHITE),
            border_color="#D8E4EE",
            focused_border_color=TEAL,
            color=INK,
            text_size=12,
            on_change=lambda e: setattr(self, "name_value", e.control.value or ""),
        )
        self.minutes_field = ft.TextField(
            label="答题时间（分钟）",
            value=self.minutes_value,
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.46, WHITE),
            border_color="#D8E4EE",
            focused_border_color=TEAL,
            color=INK,
            text_size=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=170,
            on_change=lambda e: setattr(self, "minutes_value", e.control.value or ""),
        )
        self.use_vision = ft.Checkbox(
            label="用 AI 视觉识别答案 PDF（扫描件适用，较慢）",
            value=self.use_vision_value,
            active_color=TEAL,
            on_change=lambda e: setattr(self, "use_vision_value", bool(e.control.value)),
        )
        self.progress_text = ft.Text("", size=10.5, color=FAINT)
        header = ft.Row(
            [
                ft.Container(
                    width=34,
                    height=34,
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.55, WHITE),
                    border=ft.Border.all(1, LINE_SOFT),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=17, color=INK_SOFT),
                    on_click=lambda _e: self.app.navigate("exam"),
                    ink=True,
                ),
                ft.Column(
                    [
                        eyebrow("IMPORT CENTER · 试卷导入"),
                        heading("导入一套新试卷", size=25),
                        body("上传真题 PDF、答案解析 PDF 与听力音频，AI 生成模板 JSON。", size=12),
                    ],
                    spacing=0,
                    expand=True,
                ),
                pill("AI " + ("可用" if self.app.ai.available else "未配置"), icon=ft.Icons.AUTO_AWESOME_ROUNDED, bg=SUCCESS_BG if self.app.ai.available else WARNING_BG, fg=SUCCESS if self.app.ai.available else WARNING),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        left = glass_card(
            ft.Column(
                [
                    self._upload_row(
                        "1",
                        "真题 PDF",
                        "包含题目，最好也包含答案页",
                        ft.Icons.PICTURE_AS_PDF_ROUNDED,
                        self.question_pdf,
                        lambda: self._pick_question(),
                        required=True,
                    ),
                    divider(),
                    self._upload_row(
                        "2",
                        "答案解析 PDF（可选）",
                        "答案与解析单独成册时上传；扫描件可用 AI 识别",
                        ft.Icons.FACT_CHECK_ROUNDED,
                        self.answer_pdf,
                        lambda: self._pick_answer(),
                    ),
                    divider(),
                    self._upload_row(
                        "3",
                        "听力音频（可选）",
                        "MP3 / WAV / M4A，导入后考试中播放",
                        ft.Icons.HEADPHONES_ROUNDED,
                        self.audio,
                        lambda: self._pick_audio(),
                    ),
                    divider(),
                    ft.Row(
                        [
                            ft.Text("级别", size=11, color=FAINT),
                            self._level_chip("CET-4", "四级"),
                            self._level_chip("CET-6", "六级"),
                            ft.Container(expand=True),
                            text_action("AI 设置", self.app.show_ai_settings, icon=ft.Icons.AUTO_AWESOME_ROUNDED, size=10.5),
                        ],
                        spacing=7,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.name_field,
                    ft.Row([self.minutes_field, ft.Container(expand=True)], spacing=10),
                    self.use_vision,
                    ft.Container(
                        content=ft.Row(
                            [
                                icon_box(ft.Icons.INFO_OUTLINE_ROUNDED, color=INDIGO, bg=INDIGO_LIGHT, size=32, icon_size=15, radius=10),
                                ft.Text(
                                    "模板：cet-glass-paper/v1。导入后可在本地 JSON 中查看、修改。"
                                    "答案与题目在同一 PDF 或分离 PDF 均可。",
                                    size=10.5,
                                    color=INK_SOFT,
                                    style=ft.TextStyle(height=1.55),
                                    expand=True,
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        padding=11,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.38, WHITE),
                    ),
                    self.progress_text,
                    action_button(
                        "开始解析并导入",
                        icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                        height=46,
                        font_size=13,
                        on_click=self._start_import,
                    ),
                ],
                spacing=12,
            ),
            padding=22,
            col={"xs": 12, "lg": 8},
        )
        right = glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.ACCOUNT_TREE_ROUNDED, color=TEAL, bg=TEAL_LIGHT, size=38, icon_size=18, radius=12),
                            ft.Column(
                                [
                                    ft.Text("识别流程", size=16, weight=ft.FontWeight.W_700, color=INK),
                                    body("本地解析 + AI 补全", size=10.5),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=9,
                    ),
                    divider(),
                    self._step("01", "读取 PDF", "提取题干、选项、答案页与阅读原文。"),
                    self._step("02", "AI 识别", "扫描版答案解析用视觉模型转写；自动生成中文解析与参考范文。"),
                    self._step("03", "生成 JSON", "按固定模板保存，包含听力音频、写作、阅读、翻译与答案。"),
                    self._step("04", "开始做题", "填好试卷名称与时间，导入后即可进入全真模考。"),
                    frosted_panel(
                        ft.Column(
                            [
                                ft.Text("可导入的题型", size=10.5, weight=ft.FontWeight.W_700, color=INK),
                                ft.Text(
                                    "写作 · 听力 1-25 · 选词填空 26-35 · 段落匹配 36-45 · 仔细阅读 46-55 · 翻译",
                                    size=10.5,
                                    color=MUTED,
                                    style=ft.TextStyle(height=1.55),
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=12,
                        fill=0.42,
                    ),
                    pill("所有文件仅保存在本机", icon=ft.Icons.SHIELD_ROUNDED, bg="#EEF5F2", fg=SUCCESS, size=9.5),
                ],
                spacing=13,
            ),
            padding=22,
            col={"xs": 12, "lg": 4},
        )
        return ft.Column([header, ft.ResponsiveRow([left, right], spacing=16, run_spacing=16)], spacing=16)

    def _level_chip(self, level: str, label: str) -> ft.Container:
        active = self.level == level
        return ft.Container(
            content=ft.Text(label, size=10.5, color=WHITE if active else MUTED, weight=ft.FontWeight.W_600),
            padding=ft.Padding.symmetric(horizontal=11, vertical=6),
            bgcolor=TEAL if active else ft.Colors.with_opacity(0.4, WHITE),
            border_radius=999,
            on_click=lambda _e, lv=level: self._select_level(lv),
            ink=True,
        )

    def _select_level(self, level: str) -> None:
        self.level = level
        self.minutes_value = "125" if level == "CET-4" else "130"
        self.app.render()

    def _upload_row(
        self,
        num: str,
        title: str,
        subtitle: str,
        icon: ft.IconData,
        path: Path | None,
        on_pick,
        *,
        required: bool = False,
    ) -> ft.Control:
        return ft.Row(
            [
                ft.Container(
                    width=28,
                    height=28,
                    border_radius=9,
                    bgcolor=TEAL_LIGHT,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(num, size=10, weight=ft.FontWeight.W_700, color=TEAL_DARK),
                ),
                icon_box(icon, color=TEAL, bg=TEAL_LIGHT, size=34, icon_size=16, radius=10),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(title, size=12.5, weight=ft.FontWeight.W_700, color=INK),
                                pill("必填", bg=DANGER_BG, fg=DANGER, size=8) if required else ft.Container(),
                            ],
                            spacing=6,
                        ),
                        ft.Text(
                            path.name if path else subtitle,
                            size=10,
                            color=SUCCESS if path else FAINT,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=1,
                    expand=True,
                ),
                text_action("选择", on_pick, icon=ft.Icons.UPLOAD_FILE_ROUNDED, size=10.5),
            ],
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _step(self, num: str, title: str, desc: str) -> ft.Control:
        return ft.Row(
            [
                ft.Text(num, size=9.5, color=TEAL, weight=ft.FontWeight.W_800),
                ft.Column(
                    [
                        ft.Text(title, size=11.5, weight=ft.FontWeight.W_700, color=INK),
                        ft.Text(desc, size=10, color=MUTED, style=ft.TextStyle(height=1.45)),
                    ],
                    spacing=1,
                    expand=True,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    async def _pick_pdf(self, answer: bool = False) -> None:
        files = await self.app.file_picker.pick_files(
            dialog_title="选择 PDF",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["pdf"],
            allow_multiple=False,
        )
        if not files:
            return
        path = self._file_path(files[0])
        if not path:
            self.app.notify("无法读取所选文件路径。", "error")
            return
        if answer:
            self.answer_pdf = path
        else:
            self.question_pdf = path
            if not self.name_value.strip():
                self.name_value = path.stem
        self.app.render()

    def _pick_question(self) -> None:
        self.app.page.run_task(self._pick_pdf, False)

    def _pick_answer(self) -> None:
        self.app.page.run_task(self._pick_pdf, True)

    def _pick_audio(self) -> None:
        self.app.page.run_task(self._pick_audio_async)

    async def _pick_audio_async(self) -> None:
        files = await self.app.file_picker.pick_files(
            dialog_title="选择听力音频",
            file_type=ft.FilePickerFileType.AUDIO,
            allow_multiple=False,
        )
        if not files:
            return
        path = self._file_path(files[0])
        if path:
            self.audio = path
            self.app.render()

    def _file_path(self, file: ft.FilePickerFile) -> Path | None:
        if getattr(file, "path", None):
            return Path(file.path)
        if getattr(file, "bytes", None):
            target = self.app.store.path.parent / "uploads" / (file.name or "upload.pdf")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(file.bytes)
            return target
        return None

    def _start_import(self) -> None:
        if self.busy:
            return
        if not self.question_pdf:
            self.app.notify("请先选择真题 PDF。", "warning")
            return
        name = (self.name_value or "").strip() or self.question_pdf.stem
        try:
            minutes = int((self.minutes_value or "125").strip())
        except ValueError:
            minutes = 125
        minutes = max(30, min(300, minutes))
        if not self.app.ai.available:
            self.app.notify("AI 尚未配置，将只做本地解析，不生成解析与参考范文。", "warning")
        self.busy = True
        self.progress_text.value = "准备导入…"
        self.progress_text.color = TEAL
        self.app.page.run_task(
            self._run_import,
            name,
            minutes,
            bool(self.use_vision_value) and self.app.ai.available,
        )

    async def _run_import(self, name: str, minutes: int, use_vision: bool) -> None:
        dialog_status = ft.Text("准备导入…", size=12, color=INK)
        dialog_bar = progress_track(0, height=7, color=TEAL)
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.with_opacity(0.98, WHITE),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Row(
                [
                    icon_box(ft.Icons.AUTO_AWESOME_ROUNDED, color=INDIGO, bg=INDIGO_LIGHT, size=36, icon_size=17, radius=11),
                    ft.Text("AI 正在导入试卷", size=18, weight=ft.FontWeight.W_700, color=INK),
                ],
                spacing=10,
            ),
            content=ft.Container(
                width=self.app._dialog_width(460),
                content=ft.Column(
                    [
                        dialog_status,
                        dialog_bar,
                        ft.Text(
                            "本地解析通常几秒完成；扫描版答案 PDF 的 AI 视觉识别可能需要数分钟。",
                            size=10,
                            color=FAINT,
                            style=ft.TextStyle(height=1.5),
                        ),
                    ],
                    spacing=12,
                ),
            ),
            actions=[],
        )
        self.app.page.show_dialog(dialog)

        def on_progress(message: str, value: float) -> None:
            dialog_status.value = message
            dialog_bar.value = max(0, min(1, value))
            self.progress_text.value = message
            try:
                self.app.page.update()
            except Exception:
                pass

        try:
            paper, _ = await build_imported_paper(
                self.question_pdf,
                title=name,
                level=self.level,
                duration_sec=minutes * 60,
                audio_path=self.audio,
                answer_pdf=self.answer_pdf,
                agent=self.app.ai,
                use_vision=use_vision,
                progress=on_progress,
            )
            on_progress("保存试卷与音频…", 0.99)
            self.app.library.save_imported(paper, audio_source=self.audio, cover_source=None)
            try:
                self.app.page.pop_dialog()
            except Exception:
                pass
            self.app.navigate("exam")
            self.app.notify(f"试卷已导入：{name}", "success")
        except Exception as exc:
            traceback.print_exc()
            try:
                self.app.page.pop_dialog()
            except Exception:
                pass
            self.app.notify(f"导入失败：{exc}", "error")
        finally:
            self.busy = False
