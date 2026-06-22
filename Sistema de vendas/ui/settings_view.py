"""UI Settings View."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import config
import database
from services.export_service import export_current_data, load_last_export_status
from ui.components import build_section


class SettingsView:
    def __init__(self, tab, refresh_callback):
        self.tab = tab
        self.refresh_callback = refresh_callback
        self.value_labels = {}

    def build(self):
        ctk.CTkLabel(
            self.tab,
            text="Configuracoes do sistema",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 5))

        scroll = ctk.CTkScrollableFrame(self.tab)
        scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        runtime_body = build_section(
            scroll,
            "Ambiente atual",
            "Resumo de execucao e integracoes ativas. Credenciais nunca sao exibidas.",
        )
        self._build_key_value(runtime_body, "Modo atual", "mode")
        self._build_key_value(runtime_body, "API", "api")
        self._build_key_value(runtime_body, "Arquivo do banco local", "db_file")
        self._build_key_value(runtime_body, "Credenciais Firebase", "firebase_credentials")
        self._build_key_value(runtime_body, "Exportacao para frontend", "frontend_export")
        self._build_key_value(runtime_body, "Limite de baixo estoque", "low_stock_threshold")

        export_body = build_section(
            scroll,
            "Exportacao manual",
            "Forca a mesma saida consumida pelo frontend, sem alterar o arquivo de destino existente.",
        )

        ctk.CTkButton(
            export_body,
            text="Exportar produtos/pedidos",
            command=self._run_manual_export,
            height=38,
        ).pack(anchor=tk.W, pady=(0, 12))

        self.export_status_label = ctk.CTkLabel(
            export_body,
            text="",
            justify="left",
            wraplength=700,
            anchor="w",
        )
        self.export_status_label.pack(fill=tk.X)

    def refresh(self):
        runtime = database.get_runtime_summary()
        credentials_path = runtime.get("credentials_path", config.FIREBASE_CREDENTIALS_PATH)
        credentials_status = "presente" if runtime.get("credentials_present") else "ausente"
        mode = (
            f"{str(runtime.get('mode', 'development')).upper()} / "
            f"{str(runtime.get('backend', 'desconhecido')).upper()}"
        )
        api_host = config.API_HOST or "0.0.0.0"

        self.value_labels["mode"].configure(text=mode)
        self.value_labels["api"].configure(text=f"{api_host}:{config.API_PORT}")
        self.value_labels["db_file"].configure(text=config.DB_FILE)
        self.value_labels["firebase_credentials"].configure(
            text=(
                f"{credentials_status} | projeto {runtime.get('project_id', 'desconhecido')} | "
                f"{runtime.get('credentials_source', 'desconhecido')}: {credentials_path}"
            )
        )
        self.value_labels["frontend_export"].configure(
            text="habilitada" if config.FRONTEND_EXPORT_ENABLED else "desabilitada"
        )
        self.value_labels["low_stock_threshold"].configure(text=str(config.LOW_STOCK_THRESHOLD))

        self._render_export_status(load_last_export_status())

    def _build_key_value(self, parent, label_text, key):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.X, pady=4)
        ctk.CTkLabel(
            row,
            text=label_text,
            font=ctk.CTkFont(weight="bold"),
            width=220,
            anchor="w",
        ).pack(side=tk.LEFT)
        value = ctk.CTkLabel(
            row,
            text="--",
            justify="left",
            anchor="w",
            wraplength=500,
        )
        value.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.value_labels[key] = value

    def _run_manual_export(self):
        result = export_current_data()
        self._render_export_status(result)

        if result.get("status") == "success":
            self.refresh_callback()
            messagebox.showinfo("Exportacao", result.get("message", "Exportacao concluida."))
            return

        if result.get("status") == "disabled":
            messagebox.showwarning("Exportacao", result.get("message", "Exportacao desativada."))
            return

        messagebox.showerror("Exportacao", result.get("message", "Falha na exportacao."))

    def _render_export_status(self, status):
        if not status:
            self.export_status_label.configure(
                text="Ultima exportacao: nenhuma execucao registrada.",
                text_color=("gray35", "gray70"),
            )
            return

        timestamp = status.get("timestamp", "sem horario")
        export_path = status.get("export_path", config.FRONTEND_EXPORT_PATH)
        message = status.get("message", "")
        state = status.get("status", "desconhecido")
        color = "#2e7d32" if state == "success" else "#b26a00" if state == "disabled" else "#b00020"
        self.export_status_label.configure(
            text=(
                f"Ultima exportacao: {state}\n"
                f"Horario: {timestamp}\n"
                f"Destino: {export_path}\n"
                f"Detalhe: {message}"
            ),
            text_color=color,
        )
