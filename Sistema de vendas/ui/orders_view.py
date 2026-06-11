"""Orders and logistics UI for the CustomTkinter shell."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, List

import customtkinter as ctk

from domain.order import (
    LEGACY_STATUS_ALIASES,
    STATUS_CANCELADO,
    STATUS_EMBALAGEM,
    STATUS_ENVIADO,
    STATUS_ENTREGUE,
    STATUS_PAGAMENTO_PENDENTE,
    STATUS_PAGO,
    STATUS_PENDENTE,
    STATUS_PRONTO_ENVIO,
    STATUS_SEPARACAO,
    SUPPORTED_ORDER_STATUSES,
    normalize_order,
    normalize_status,
    parse_date,
)
from services import order_service
from ui.components import build_treeview_with_scrollbar


STATUS_LABELS = {
    STATUS_PENDENTE: "Pendente",
    STATUS_PAGAMENTO_PENDENTE: "Pagamento pendente",
    STATUS_PAGO: "Pago",
    STATUS_SEPARACAO: "Em separacao",
    STATUS_EMBALAGEM: "Embalado",
    STATUS_PRONTO_ENVIO: "Pronto para envio",
    STATUS_ENVIADO: "Enviado",
    STATUS_ENTREGUE: "Entregue",
    STATUS_CANCELADO: "Cancelado",
    "devolvido": "Devolvido",
}

ACTION_TEXT = {
    STATUS_SEPARACAO: "Iniciar separacao",
    STATUS_EMBALAGEM: "Marcar embalado",
    STATUS_PRONTO_ENVIO: "Marcar pronto para envio",
    STATUS_ENVIADO: "Marcar enviado",
    STATUS_ENTREGUE: "Marcar entregue",
    STATUS_CANCELADO: "Cancelar pedido",
}

ROW_TAGS = {
    STATUS_PENDENTE: ("pendente", "#7f8c8d"),
    STATUS_PAGAMENTO_PENDENTE: ("pendente", "#7f8c8d"),
    STATUS_PAGO: ("pago", "#2980b9"),
    STATUS_SEPARACAO: ("processando", "#8e44ad"),
    STATUS_EMBALAGEM: ("processando", "#8e44ad"),
    STATUS_PRONTO_ENVIO: ("pronto", "#d35400"),
    STATUS_ENVIADO: ("enviado", "#27ae60"),
    STATUS_ENTREGUE: ("finalizado", "#16a085"),
    STATUS_CANCELADO: ("cancelado", "#c0392b"),
    "devolvido": ("cancelado", "#c0392b"),
}


def _customer_name(order: Dict[str, Any]) -> str:
    normalized = normalize_order(order)
    return normalized.get("customer_name", "Cliente")


def _customer_email(order: Dict[str, Any]) -> str:
    normalized = normalize_order(order)
    return normalized.get("customer_email", "")


def _format_currency(value: Any) -> str:
    try:
        return f"R$ {float(value or 0):.2f}"
    except (TypeError, ValueError):
        return "R$ 0.00"


def _format_datetime(value: Any) -> str:
    if not value:
        return "-"
    try:
        return parse_date(value).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)


def _format_status(status: Any) -> str:
    normalized = normalize_status(status, "")
    if normalized in STATUS_LABELS:
        return STATUS_LABELS[normalized]
    alias = LEGACY_STATUS_ALIASES.get(str(status or "").strip().lower())
    if alias in STATUS_LABELS:
        return STATUS_LABELS[alias]
    return str(status or "-").strip().title() or "-"


def _order_items(order: Dict[str, Any]) -> List[Dict[str, Any]]:
    return normalize_order(order).get("items", [])


def get_order_action_specs(order: Dict[str, Any]) -> List[Dict[str, str]]:
    normalized = normalize_order(order)
    current_status = normalized.get("status", STATUS_PENDENTE)
    actions: List[Dict[str, str]] = []

    for target_status in (
        STATUS_SEPARACAO,
        STATUS_EMBALAGEM,
        STATUS_PRONTO_ENVIO,
        STATUS_ENVIADO,
        STATUS_ENTREGUE,
        STATUS_CANCELADO,
    ):
        if target_status == current_status:
            continue
        result = order_service.validate_status_transition(current_status, target_status)
        if result.get("ok"):
            actions.append(
                {
                    "target_status": target_status,
                    "label": ACTION_TEXT[target_status],
                }
            )
    return actions


def get_next_action_label(order: Dict[str, Any]) -> str:
    actions = get_order_action_specs(order)
    return actions[0]["label"] if actions else "-"


class OrdersView:
    def __init__(self, root, tab, refresh_callback):
        self.root = root
        self.tab = tab
        self.refresh_callback = refresh_callback
        self.tree = None
        self.search_var = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="Todos")

    def build(self):
        top_frame = ctk.CTkFrame(self.tab, fg_color="transparent")
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 12))

        ctk.CTkLabel(
            top_frame,
            text="Pedidos, expedicao e acompanhamento operacional",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side=tk.LEFT)

        ctk.CTkButton(
            top_frame,
            text="Ver detalhes do pedido",
            command=self.open_selected_order,
        ).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(
            top_frame,
            text="Marcar pedido selecionado como enviado",
            command=self.dispatch_selected_order_to_sent,
            fg_color="#00b894",
            hover_color="#55efc4",
        ).pack(side=tk.RIGHT, padx=5)

        filters_frame = ctk.CTkFrame(self.tab)
        filters_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        filters_frame.grid_columnconfigure(0, weight=3)
        filters_frame.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(filters_frame, text="Busca").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        search_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self.search_var,
            placeholder_text="Buscar por pedido, cliente ou email",
        )
        search_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        search_entry.bind("<KeyRelease>", lambda _event: self.load_orders())

        ctk.CTkLabel(filters_frame, text="Status").grid(row=0, column=1, sticky="w", padx=12, pady=(12, 0))
        status_menu = ctk.CTkOptionMenu(
            filters_frame,
            values=["Todos", *[_format_status(status) for status in sorted(SUPPORTED_ORDER_STATUSES)]],
            variable=self.status_var,
            command=lambda _value: self.load_orders(),
        )
        status_menu.grid(row=1, column=1, sticky="ew", padx=12, pady=(0, 12))

        table_frame = ctk.CTkFrame(self.tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "customer", "total", "status", "created_at", "next_action")
        self.tree, scrollbar = build_treeview_with_scrollbar(table_frame, columns)

        headings = {
            "id": ("Order ID", 120, tk.CENTER),
            "customer": ("Customer", 220, tk.W),
            "total": ("Total", 110, tk.CENTER),
            "status": ("Status", 150, tk.CENTER),
            "created_at": ("Created At", 160, tk.CENTER),
            "next_action": ("Next Action", 220, tk.W),
        }
        for column, (label, width, anchor) in headings.items():
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda _event: self.open_selected_order())

    def _filtered_orders(self) -> List[Dict[str, Any]]:
        query = self.search_var.get().strip().lower()
        selected_status = self.status_var.get().strip()
        orders = sorted(order_service.list_orders(), key=lambda order: order.get("id", ""), reverse=True)

        def matches(order: Dict[str, Any]) -> bool:
            if query:
                haystack = " ".join(
                    [
                        str(order.get("id", "") or ""),
                        _customer_name(order),
                        _customer_email(order),
                    ]
                ).lower()
                if query not in haystack:
                    return False

            if selected_status and selected_status != "Todos":
                if _format_status(order.get("status")) != selected_status:
                    return False

            return True

        return [order for order in orders if matches(order)]

    def load_orders(self):
        if not self.tree:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for order in self._filtered_orders():
            status = normalize_status(order.get("status"))
            values = (
                order.get("id", ""),
                _customer_name(order),
                _format_currency(order.get("total", 0)),
                _format_status(status),
                _format_datetime(order.get("created_at")),
                get_next_action_label(order),
            )
            row_id = self.tree.insert("", tk.END, values=values)
            if status in ROW_TAGS:
                self.tree.item(row_id, tags=(ROW_TAGS[status][0],))

        for tag_name, color in {
            "pendente": "#7f8c8d",
            "pago": "#2980b9",
            "processando": "#8e44ad",
            "pronto": "#d35400",
            "enviado": "#27ae60",
            "finalizado": "#16a085",
            "cancelado": "#c0392b",
        }.items():
            self.tree.tag_configure(tag_name, foreground=color)

    def get_selected_order(self):
        if not self.tree:
            return None
        selected = self.tree.selection()
        if not selected:
            return None
        order_id = self.tree.item(selected[0], "values")[0]
        return order_service.get_order(order_id)

    def open_selected_order(self):
        order = self.get_selected_order()
        if not order:
            messagebox.showwarning("Selecao", "Selecione um pedido para visualizar.")
            return
        self.open_order_modal(order)

    def dispatch_selected_order_to_sent(self):
        order = self.get_selected_order()
        if not order:
            messagebox.showwarning("Fila vazia", "Selecione um pedido para processar.")
            return

        validation = order_service.validate_status_transition(order.get("status"), STATUS_ENVIADO)
        if not validation.get("ok"):
            messagebox.showwarning("Transicao invalida", validation.get("message", "Nao e possivel marcar como enviado."))
            return

        confirmed = messagebox.askyesno(
            "Confirmar envio",
            f"Deseja marcar o pedido {order.get('id')} como enviado?",
        )
        if not confirmed:
            return

        self._apply_status_change(order.get("id", ""), STATUS_ENVIADO)

    def _apply_status_change(self, order_id: str, target_status: str, modal=None):
        result = order_service.update_status(order_id, target_status)
        if not result.get("ok"):
            messagebox.showerror("Erro", result.get("message", "Nao foi possivel atualizar o pedido."), parent=modal)
            return

        self.refresh_callback()
        if modal is not None and modal.winfo_exists():
            modal.destroy()
            updated_order = order_service.get_order(order_id)
            if updated_order:
                self.open_order_modal(updated_order)

        messagebox.showinfo("Atualizado", result.get("message", "Pedido atualizado."))

    def open_order_modal(self, order: Dict[str, Any]):
        normalized = normalize_order(order)
        win = ctk.CTkToplevel(self.root)
        win.title(f"Pedido {normalized.get('id', '')}")
        win.geometry("900x760")
        win.transient(self.root)
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            scroll,
            text=f"Pedido {normalized.get('id', '')}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor=tk.W, pady=(0, 4))
        ctk.CTkLabel(
            scroll,
            text=f"Status atual: {_format_status(normalized.get('status'))}",
            text_color=("gray35", "gray70"),
        ).pack(anchor=tk.W, pady=(0, 16))

        customer_card = ctk.CTkFrame(scroll, corner_radius=12)
        customer_card.pack(fill=tk.X, pady=(0, 12))
        ctk.CTkLabel(
            customer_card,
            text="Customer info",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor=tk.W, padx=16, pady=(14, 8))
        for label, value in (
            ("Nome", normalized.get("customer_name") or "-"),
            ("Email", normalized.get("customer_email") or "-"),
            ("Telefone", normalized.get("customer_phone") or "-"),
            ("Endereco", normalized.get("customer_address") or "-"),
            ("Criado em", _format_datetime(normalized.get("created_at"))),
        ):
            ctk.CTkLabel(customer_card, text=f"{label}: {value}", justify="left").pack(anchor=tk.W, padx=16, pady=2)

        items_card = ctk.CTkFrame(scroll, corner_radius=12)
        items_card.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        ctk.CTkLabel(
            items_card,
            text="Items",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor=tk.W, padx=16, pady=(14, 8))

        items_table_frame = ctk.CTkFrame(items_card)
        items_table_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))
        items_tree, scrollbar = build_treeview_with_scrollbar(
            items_table_frame,
            ("product", "quantity", "unit_price", "line_total"),
        )
        for column, label, width, anchor in (
            ("product", "Produto", 320, tk.W),
            ("quantity", "Qtd.", 70, tk.CENTER),
            ("unit_price", "Unitario", 120, tk.CENTER),
            ("line_total", "Subtotal", 120, tk.CENTER),
        ):
            items_tree.heading(column, text=label)
            items_tree.column(column, width=width, anchor=anchor)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for item in _order_items(normalized):
            quantity = int(item.get("quantity", 1))
            unit_price = float(item.get("unit_price", 0))
            items_tree.insert(
                "",
                tk.END,
                values=(
                    item.get("product_name", "Item"),
                    quantity,
                    _format_currency(unit_price),
                    _format_currency(quantity * unit_price),
                ),
            )

        summary_card = ctk.CTkFrame(scroll, corner_radius=12)
        summary_card.pack(fill=tk.X, pady=(0, 12))
        ctk.CTkLabel(
            summary_card,
            text="Resumo financeiro",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor=tk.W, padx=16, pady=(14, 8))
        for label, value in (
            ("Subtotal", _format_currency(normalized.get("subtotal", 0))),
            ("Frete", _format_currency(normalized.get("shipping", 0))),
            ("Desconto", _format_currency(normalized.get("discount_total", 0))),
            ("Cupom", normalized.get("coupon_code") or "-"),
            ("Total", _format_currency(normalized.get("total", 0))),
        ):
            ctk.CTkLabel(summary_card, text=f"{label}: {value}").pack(anchor=tk.W, padx=16, pady=2)

        actions_card = ctk.CTkFrame(scroll, corner_radius=12)
        actions_card.pack(fill=tk.X, pady=(0, 12))
        ctk.CTkLabel(
            actions_card,
            text="Acoes disponiveis",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor=tk.W, padx=16, pady=(14, 8))

        actions = get_order_action_specs(normalized)
        if not actions:
            ctk.CTkLabel(
                actions_card,
                text="Nenhuma transicao disponivel para este status.",
                text_color=("gray40", "gray70"),
            ).pack(anchor=tk.W, padx=16, pady=(0, 14))
        else:
            buttons_row = ctk.CTkFrame(actions_card, fg_color="transparent")
            buttons_row.pack(fill=tk.X, padx=16, pady=(0, 14))
            for action in actions:
                colors = {}
                if action["target_status"] == STATUS_CANCELADO:
                    colors = {"fg_color": "#c0392b", "hover_color": "#e74c3c"}
                elif action["target_status"] == STATUS_ENVIADO:
                    colors = {"fg_color": "#00b894", "hover_color": "#55efc4"}

                ctk.CTkButton(
                    buttons_row,
                    text=action["label"],
                    command=lambda target=action["target_status"]: self._confirm_status_change(normalized, target, win),
                    **colors,
                ).pack(side=tk.LEFT, padx=(0, 8))

    def _confirm_status_change(self, order: Dict[str, Any], target_status: str, modal):
        label = ACTION_TEXT.get(target_status, "Atualizar status")
        confirmed = messagebox.askyesno(
            "Confirmar acao",
            f"{label} para o pedido {order.get('id')}?",
            parent=modal,
        )
        if confirmed:
            self._apply_status_change(order.get("id", ""), target_status, modal=modal)
