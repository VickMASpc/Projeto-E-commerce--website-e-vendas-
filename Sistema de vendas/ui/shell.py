"""UI shell helpers."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk


TAB_DEFINITIONS = (
    ("Dashboard", "dashboard"),
    ("Estoque & Produtos", "products"),
    ("Pedidos & Logistica", "orders"),
    ("Cupons", "coupons"),
    ("Configuracoes", "settings"),
)


def configure_treeview_style() -> None:
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")

    is_dark_mode = ctk.get_appearance_mode() == "Dark"
    bg_color = "#2b2b2b" if is_dark_mode else "#ebebeb"
    fg_color = "#ffffff" if is_dark_mode else "#000000"
    header_bg = "#333333" if is_dark_mode else "#d9d9d9"
    header_fg = "#ffffff" if is_dark_mode else "#000000"

    style.configure(
        "Treeview",
        background=bg_color,
        foreground=fg_color,
        fieldbackground=bg_color,
        rowheight=25,
        borderwidth=0,
        font=("Helvetica", 11),
    )
    style.configure(
        "Treeview.Heading",
        background=header_bg,
        foreground=header_fg,
        relief="flat",
        font=("Helvetica", 12, "bold"),
    )
    style.map("Treeview", background=[("selected", "#1f538d")])


def build_tabview(root) -> tuple[ctk.CTkTabview, dict[str, ctk.CTkFrame]]:
    notebook = ctk.CTkTabview(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tabs = {}
    for label, key in TAB_DEFINITIONS:
        notebook.add(label)
        tabs[key] = notebook.tab(label)

    return notebook, tabs
