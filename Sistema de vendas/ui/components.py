"""Reusable CustomTkinter components for the sales system UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk


def build_section(parent, title: str, description: str | None = None) -> ctk.CTkFrame:
    section = ctk.CTkFrame(parent, corner_radius=12)
    section.pack(fill=tk.X, pady=(0, 14))

    ctk.CTkLabel(
        section,
        text=title,
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(anchor=tk.W, padx=16, pady=(14, 2))

    if description:
        ctk.CTkLabel(
            section,
            text=description,
            text_color=("gray40", "gray70"),
            justify="left",
            wraplength=620,
        ).pack(anchor=tk.W, padx=16, pady=(0, 10))

    body = ctk.CTkFrame(section, fg_color="transparent")
    body.pack(fill=tk.X, padx=16, pady=(0, 14))
    return body


def build_error_box(parent) -> ctk.CTkLabel:
    label = ctk.CTkLabel(
        parent,
        text="",
        text_color="#b00020",
        justify="left",
        wraplength=620,
        anchor="w",
    )
    label.pack(fill=tk.X, padx=4, pady=(0, 12))
    label.pack_forget()
    return label


def set_error_text(label: ctk.CTkLabel, message: str) -> None:
    if message.strip():
        label.configure(text=message)
        label.pack(fill=tk.X, padx=4, pady=(0, 12))
    else:
        label.configure(text="")
        label.pack_forget()


def build_labeled_entry(parent, label: str, value: str = "") -> ctk.CTkEntry:
    ctk.CTkLabel(parent, text=label).pack(anchor=tk.W, pady=(6, 0))
    entry = ctk.CTkEntry(parent)
    entry.pack(fill=tk.X, pady=(0, 10))
    entry.insert(0, value)
    return entry


def build_labeled_textbox(parent, label: str, value: str = "", height: int = 80) -> ctk.CTkTextbox:
    ctk.CTkLabel(parent, text=label).pack(anchor=tk.W, pady=(6, 0))
    textbox = ctk.CTkTextbox(parent, height=height, wrap="word")
    textbox.pack(fill=tk.X, pady=(0, 10))
    textbox.insert("1.0", value)
    return textbox


def build_labeled_optionmenu(parent, label: str, values: list[str], selected: str) -> ctk.CTkOptionMenu:
    ctk.CTkLabel(parent, text=label).pack(anchor=tk.W, pady=(6, 0))
    option = ctk.CTkOptionMenu(parent, values=values)
    option.pack(fill=tk.X, pady=(0, 10))
    option.set(selected or values[0])
    return option


def build_treeview_with_scrollbar(parent, columns: tuple[str, ...]) -> tuple[ttk.Treeview, ctk.CTkScrollbar]:
    tree = ttk.Treeview(parent, columns=columns, show="headings")
    scrollbar = ctk.CTkScrollbar(parent, orientation="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    return tree, scrollbar
