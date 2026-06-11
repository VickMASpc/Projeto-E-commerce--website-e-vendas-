"""Coupons management UI for the CustomTkinter shell."""

from __future__ import annotations

import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import Any, Dict, List, Optional

import customtkinter as ctk

import database
from services.coupon_service import CouponService
from ui.components import (
    build_error_box,
    build_labeled_entry,
    build_labeled_optionmenu,
    build_section,
    build_treeview_with_scrollbar,
    set_error_text,
)


COUPON_TYPES = ["percent", "fixed"]
STATUS_FILTERS = ["Todos", "Ativos", "Inativos"]
CODE_PATTERN = re.compile(r"^[A-Z0-9_-]+$")


def _format_money(value: Any) -> str:
    if value in (None, ""):
        return "-"
    try:
        return f"R$ {float(value):.2f}"
    except (TypeError, ValueError):
        return "-"


def _format_value(coupon: Dict[str, Any]) -> str:
    value = float(coupon.get("value", 0) or 0)
    if coupon.get("type") == "percent":
        return f"{value:.0f}%"
    return _format_money(value)


def _format_usage(coupon: Dict[str, Any]) -> str:
    used = int(coupon.get("used_count", 0) or 0)
    limit = coupon.get("usage_limit")
    return f"{used}/{int(limit)}" if limit is not None else f"{used}/-"


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1]
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _format_datetime(value: Any) -> str:
    parsed = _parse_iso_datetime(value)
    if not parsed:
        return "-"
    return parsed.strftime("%d/%m/%Y %H:%M")


class CouponsView:
    def __init__(self, root, tab, refresh_callback):
        self.root = root
        self.tab = tab
        self.refresh_callback = refresh_callback
        self.tree = None
        self.search_var = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="Todos")
        self.type_var = ctk.StringVar(value="Todos")

    def _service(self) -> CouponService:
        return CouponService(database._get_repo())

    def build(self):
        top_frame = ctk.CTkFrame(self.tab, fg_color="transparent")
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 12))

        ctk.CTkLabel(
            top_frame,
            text="Gestao de cupons e regras promocionais",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side=tk.LEFT)

        ctk.CTkButton(
            top_frame,
            text="Testar validacao",
            command=self.validate_selected_coupon,
        ).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(
            top_frame,
            text="Ativar/desativar",
            command=self.toggle_selected_coupon_status,
        ).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(
            top_frame,
            text="Editar cupom",
            command=self.edit_selected_coupon,
        ).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(
            top_frame,
            text="Criar cupom",
            command=lambda: self.open_coupon_modal(),
        ).pack(side=tk.RIGHT, padx=5)

        filters_frame = ctk.CTkFrame(self.tab)
        filters_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        filters_frame.grid_columnconfigure(0, weight=4)
        filters_frame.grid_columnconfigure(1, weight=2)
        filters_frame.grid_columnconfigure(2, weight=2)

        ctk.CTkLabel(filters_frame, text="Busca").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        search_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self.search_var,
            placeholder_text="Buscar por codigo do cupom",
        )
        search_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        search_entry.bind("<KeyRelease>", lambda _event: self.load_coupons())

        ctk.CTkLabel(filters_frame, text="Status").grid(row=0, column=1, sticky="w", padx=12, pady=(12, 0))
        ctk.CTkOptionMenu(
            filters_frame,
            values=STATUS_FILTERS,
            variable=self.status_var,
            command=lambda _value: self.load_coupons(),
        ).grid(row=1, column=1, sticky="ew", padx=12, pady=(0, 12))

        ctk.CTkLabel(filters_frame, text="Tipo").grid(row=0, column=2, sticky="w", padx=12, pady=(12, 0))
        ctk.CTkOptionMenu(
            filters_frame,
            values=["Todos", "percent", "fixed"],
            variable=self.type_var,
            command=lambda _value: self.load_coupons(),
        ).grid(row=1, column=2, sticky="ew", padx=12, pady=(0, 12))

        table_frame = ctk.CTkFrame(self.tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("code", "type", "value", "active", "min_order", "max_discount", "usage", "expires_at")
        self.tree, scrollbar = build_treeview_with_scrollbar(table_frame, columns)

        headings = {
            "code": ("Code", 140, tk.W),
            "type": ("Type", 90, tk.CENTER),
            "value": ("Value", 110, tk.CENTER),
            "active": ("Active", 90, tk.CENTER),
            "min_order": ("Min Order", 110, tk.CENTER),
            "max_discount": ("Max Discount", 120, tk.CENTER),
            "usage": ("Usage", 90, tk.CENTER),
            "expires_at": ("Expires At", 150, tk.CENTER),
        }
        for column, (label, width, anchor) in headings.items():
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected_coupon())

    def _filtered_coupons(self) -> List[Dict[str, Any]]:
        query = self.search_var.get().strip().lower()
        selected_status = self.status_var.get().strip()
        selected_type = self.type_var.get().strip()
        coupons = sorted(self._service().list_coupons(), key=lambda coupon: coupon.get("code", ""))

        def matches(coupon: Dict[str, Any]) -> bool:
            if query and query not in str(coupon.get("code", "")).lower():
                return False
            if selected_status == "Ativos" and not coupon.get("active"):
                return False
            if selected_status == "Inativos" and coupon.get("active"):
                return False
            if selected_type != "Todos" and coupon.get("type") != selected_type:
                return False
            return True

        return [coupon for coupon in coupons if matches(coupon)]

    def load_coupons(self):
        if not self.tree:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for coupon in self._filtered_coupons():
            row_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    coupon.get("code", ""),
                    str(coupon.get("type", "")).title(),
                    _format_value(coupon),
                    "Sim" if coupon.get("active") else "Nao",
                    _format_money(coupon.get("min_order_total")),
                    _format_money(coupon.get("max_discount")),
                    _format_usage(coupon),
                    _format_datetime(coupon.get("expires_at")),
                ),
            )
            self.tree.item(row_id, tags=("active" if coupon.get("active") else "inactive",))

        self.tree.tag_configure("active", foreground="#1f7a4d")
        self.tree.tag_configure("inactive", foreground="#a33a3a")

    def get_selected_coupon(self) -> Optional[Dict[str, Any]]:
        if not self.tree:
            return None
        selected = self.tree.selection()
        if not selected:
            return None
        code = self.tree.item(selected[0], "values")[0]
        return self._service().get_coupon(code)

    def edit_selected_coupon(self):
        coupon = self.get_selected_coupon()
        if not coupon:
            messagebox.showwarning("Selecao", "Selecione um cupom para editar.")
            return
        self.open_coupon_modal(coupon)

    def toggle_selected_coupon_status(self):
        coupon = self.get_selected_coupon()
        if not coupon:
            messagebox.showwarning("Selecao", "Selecione um cupom para atualizar o status.")
            return

        target_active = not bool(coupon.get("active"))
        action_text = "ativar" if target_active else "desativar"
        confirmed = messagebox.askyesno(
            "Confirmar alteracao",
            f"Deseja {action_text} o cupom {coupon.get('code')}?",
        )
        if not confirmed:
            return

        if target_active:
            result = self._service().update_coupon(coupon["code"], {"active": True})
        else:
            result = self._service().deactivate_coupon(coupon["code"])

        if not result.get("ok"):
            messagebox.showerror("Erro", result.get("message", "Nao foi possivel atualizar o cupom."))
            return

        self.refresh_callback()
        messagebox.showinfo("Atualizado", f"Cupom {coupon.get('code')} {action_text}do com sucesso.")

    def validate_selected_coupon(self):
        coupon = self.get_selected_coupon()
        if not coupon:
            messagebox.showwarning("Selecao", "Selecione um cupom para testar a validacao.")
            return
        self.open_validation_modal(coupon)

    def open_validation_modal(self, coupon: Dict[str, Any]):
        win = ctk.CTkToplevel(self.root)
        win.title(f"Validar cupom {coupon.get('code')}")
        win.geometry("420x280")
        win.transient(self.root)
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text=f"Validar cupom {coupon.get('code')}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor=tk.W, pady=(0, 6))
        ctk.CTkLabel(
            frame,
            text="Informe um subtotal para executar a mesma regra usada pela API /coupon/validate.",
            justify="left",
            wraplength=340,
            text_color=("gray40", "gray70"),
        ).pack(anchor=tk.W, pady=(0, 12))

        error_label = build_error_box(frame)
        subtotal_entry = build_labeled_entry(
            frame,
            "Subtotal do pedido",
            str(coupon.get("min_order_total") or 0),
        )
        result_label = ctk.CTkLabel(frame, text="", justify="left", anchor="w", wraplength=340)
        result_label.pack(fill=tk.X, pady=(8, 0))

        def run_validation():
            set_error_text(error_label, "")
            result_label.configure(text="")
            try:
                subtotal = float(subtotal_entry.get().strip().replace(",", "."))
                if subtotal < 0:
                    raise ValueError
            except ValueError:
                set_error_text(error_label, "Informe um subtotal numerico maior ou igual a zero.")
                return

            result = self._service().validate_coupon(coupon.get("code", ""), subtotal)
            message = [
                f"Valido: {'Sim' if result.get('valid') else 'Nao'}",
                f"Mensagem: {result.get('message', '-')}",
                f"Desconto: {_format_money(result.get('discount'))}",
                f"Total ajustado: {_format_money(result.get('adjusted_total'))}",
            ]
            result_label.configure(text="\n".join(message))

        ctk.CTkButton(
            frame,
            text="Executar validacao",
            command=run_validation,
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor=tk.W, pady=(14, 0))

    def open_coupon_modal(self, coupon: Optional[Dict[str, Any]] = None):
        is_edit = coupon is not None
        values = dict(coupon or {})

        win = ctk.CTkToplevel(self.root)
        win.title("Editar cupom" if is_edit else "Criar cupom")
        win.geometry("720x760")
        win.transient(self.root)
        win.grab_set()

        form_frame = ctk.CTkScrollableFrame(win)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            form_frame,
            text="Configuracao de cupom",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor=tk.W, pady=(0, 8))
        ctk.CTkLabel(
            form_frame,
            text="Os campos sao validados antes do salvamento e usam a mesma estrutura de dados do servico de cupons.",
            text_color=("gray40", "gray70"),
            justify="left",
            wraplength=620,
        ).pack(anchor=tk.W, pady=(0, 12))

        error_label = build_error_box(form_frame)

        basic_body = build_section(form_frame, "Basico", "Defina o identificador, o tipo de desconto e o estado operacional.")
        code_entry = build_labeled_entry(basic_body, "Codigo", str(values.get("code", "")))
        if is_edit:
            code_entry.configure(state="disabled")
        type_menu = build_labeled_optionmenu(
            basic_body,
            "Tipo",
            COUPON_TYPES,
            str(values.get("type", "percent") or "percent"),
        )
        value_entry = build_labeled_entry(basic_body, "Valor", str(values.get("value", 0) or 0))
        active_var = ctk.BooleanVar(value=bool(values.get("active")))
        ctk.CTkCheckBox(basic_body, text="Cupom ativo", variable=active_var).pack(anchor=tk.W, pady=(4, 2))

        rules_body = build_section(form_frame, "Regras", "Controle piso minimo, teto de desconto e limite de uso.")
        min_order_entry = build_labeled_entry(
            rules_body,
            "Pedido minimo (R$)",
            str(values.get("min_order_total", 0) or 0),
        )
        max_discount_entry = build_labeled_entry(
            rules_body,
            "Desconto maximo (R$) - opcional",
            "" if values.get("max_discount") is None else str(values.get("max_discount")),
        )
        usage_limit_entry = build_labeled_entry(
            rules_body,
            "Limite de uso - opcional",
            "" if values.get("usage_limit") is None else str(values.get("usage_limit")),
        )
        used_count_entry = build_labeled_entry(
            rules_body,
            "Uso atual",
            str(values.get("used_count", 0) or 0),
        )

        schedule_body = build_section(
            form_frame,
            "Agenda",
            "Use datas ISO como 2026-06-11T10:00:00. Campos vazios mantem o cupom sem restricao nesse limite.",
        )
        starts_at_entry = build_labeled_entry(schedule_body, "Inicio - opcional", str(values.get("starts_at") or ""))
        expires_at_entry = build_labeled_entry(schedule_body, "Expira em - opcional", str(values.get("expires_at") or ""))

        def save_coupon():
            set_error_text(error_label, "")
            payload = {
                "code": values.get("code") if is_edit else code_entry.get().strip(),
                "type": type_menu.get().strip().lower(),
                "value": value_entry.get().strip(),
                "active": active_var.get(),
                "min_order_total": min_order_entry.get().strip(),
                "max_discount": max_discount_entry.get().strip(),
                "usage_limit": usage_limit_entry.get().strip(),
                "used_count": used_count_entry.get().strip(),
                "starts_at": starts_at_entry.get().strip(),
                "expires_at": expires_at_entry.get().strip(),
            }

            message = self._validate_form_payload(payload)
            if message:
                set_error_text(error_label, message)
                return

            service_payload = dict(payload)
            if service_payload["max_discount"] == "":
                service_payload["max_discount"] = None
            if service_payload["usage_limit"] == "":
                service_payload["usage_limit"] = None
            if service_payload["starts_at"] == "":
                service_payload["starts_at"] = None
            if service_payload["expires_at"] == "":
                service_payload["expires_at"] = None

            service = self._service()
            result = (
                service.update_coupon(coupon["code"], service_payload)
                if is_edit
                else service.create_coupon(service_payload)
            )
            if not result.get("ok"):
                set_error_text(error_label, result.get("message", "Nao foi possivel salvar o cupom."))
                return

            self.refresh_callback()
            win.destroy()
            messagebox.showinfo(
                "Sucesso",
                f"Cupom {result['coupon'].get('code')} salvo com sucesso.",
            )

        ctk.CTkButton(
            form_frame,
            text="Salvar cupom",
            command=save_coupon,
            font=ctk.CTkFont(weight="bold"),
            height=40,
        ).pack(fill=tk.X, pady=(10, 10))

    def _validate_form_payload(self, payload: Dict[str, Any]) -> str:
        code = str(payload.get("code", "")).strip().upper()
        if not code:
            return "O codigo do cupom e obrigatorio."
        if not CODE_PATTERN.match(code):
            return "Use apenas letras, numeros, hifen ou underscore no codigo."

        coupon_type = str(payload.get("type", "")).strip().lower()
        if coupon_type not in COUPON_TYPES:
            return "Selecione um tipo de cupom valido."

        value = self._parse_float(payload.get("value"), "Valor")
        if value is None:
            return "Informe um valor numerico valido para o desconto."
        if value <= 0:
            return "O valor do cupom precisa ser maior que zero."
        if coupon_type == "percent" and value > 100:
            return "Cupons percentuais aceitam no maximo 100."

        min_order_total = self._parse_float(payload.get("min_order_total"), "Pedido minimo")
        if min_order_total is None or min_order_total < 0:
            return "O pedido minimo precisa ser um numero maior ou igual a zero."

        max_discount = payload.get("max_discount")
        if str(max_discount).strip():
            parsed_max_discount = self._parse_float(max_discount, "Desconto maximo")
            if parsed_max_discount is None or parsed_max_discount < 0:
                return "O desconto maximo precisa ser um numero maior ou igual a zero."
        else:
            parsed_max_discount = None

        usage_limit = payload.get("usage_limit")
        if str(usage_limit).strip():
            parsed_usage_limit = self._parse_int(usage_limit)
            if parsed_usage_limit is None or parsed_usage_limit < 0:
                return "O limite de uso precisa ser um numero inteiro maior ou igual a zero."
        else:
            parsed_usage_limit = None

        parsed_used_count = self._parse_int(payload.get("used_count"))
        if parsed_used_count is None or parsed_used_count < 0:
            return "O uso atual precisa ser um numero inteiro maior ou igual a zero."
        if parsed_usage_limit is not None and parsed_used_count > parsed_usage_limit:
            return "O uso atual nao pode ser maior que o limite de uso."

        starts_at = payload.get("starts_at")
        expires_at = payload.get("expires_at")
        parsed_start = None
        parsed_expiry = None
        if str(starts_at).strip():
            parsed_start = _parse_iso_datetime(starts_at)
            if not parsed_start:
                return "A data de inicio precisa estar em formato ISO valido."
        if str(expires_at).strip():
            parsed_expiry = _parse_iso_datetime(expires_at)
            if not parsed_expiry:
                return "A data de expiracao precisa estar em formato ISO valido."
        if parsed_start and parsed_expiry and parsed_expiry < parsed_start:
            return "A expiracao nao pode ser anterior a data de inicio."
        if coupon_type == "fixed" and parsed_max_discount is not None and parsed_max_discount < value:
            return "Para cupom fixo, o desconto maximo nao pode ser menor que o valor do cupom."

        return ""

    @staticmethod
    def _parse_float(value: Any, _label: str) -> Optional[float]:
        try:
            return float(str(value).strip().replace(",", "."))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        try:
            raw = float(str(value).strip().replace(",", "."))
            if not raw.is_integer():
                return None
            return int(raw)
        except (TypeError, ValueError):
            return None
