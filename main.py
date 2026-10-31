"""Application entry point.

Run in development:
    flet run main.py

Package for Windows:
    flet pack main.py --name CET-Glass-Lab ...
"""
from __future__ import annotations

import flet as ft

from cetapp.app import main as app_main


def main(page: ft.Page) -> None:
    app_main(page)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
