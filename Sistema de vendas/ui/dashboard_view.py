"""UI Dashboard View."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

import config
import database


class DashboardView:
    def __init__(self, tab, refresh_callback):
        self.tab = tab
        self.refresh_callback = refresh_callback

    def build(self):
        ctk.CTkLabel(
            self.tab,
            text="Resumo operacional do e-commerce",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 5))

        scroll = ctk.CTkScrollableFrame(self.tab)
        scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill=tk.X, pady=(10, 5))
        for col in range(4):
            row1.columnconfigure(col, weight=1)

        self.lbl_receita = self._build_kpi_card(row1, "Receita total (R$)", col=0)
        self.lbl_total_prod = self._build_kpi_card(row1, "Total de produtos", col=1)
        self.lbl_ticket = self._build_kpi_card(row1, "Ticket medio (R$)", col=2)
        self.lbl_pedidos_hoje = self._build_kpi_card(
            row1,
            "Pedidos hoje",
            color="#3498db",
            col=3,
        )

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill=tk.X, pady=(0, 10))
        for col in range(4):
            row2.columnconfigure(col, weight=1)

        self.lbl_baixo_estoque = self._build_kpi_card(
            row2,
            f"Baixo estoque (<{config.LOW_STOCK_THRESHOLD})",
            color="#e74c3c",
            col=0,
        )
        self.lbl_pedidos_pendentes = self._build_kpi_card(
            row2,
            "Aguardando envio",
            color="#f39c12",
            col=1,
        )
        self.lbl_pagos = self._build_kpi_card(
            row2,
            "Pedidos pagos",
            color="#2ecc71",
            col=2,
        )
        self.lbl_enviados = self._build_kpi_card(
            row2,
            "Pedidos enviados",
            color="#1abc9c",
            col=3,
        )

        tables_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        tables_frame.pack(fill=tk.X, pady=5)
        for col in range(3):
            tables_frame.columnconfigure(col, weight=1)

        self.lbl_activity = self._build_text_card(
            tables_frame,
            "Atividade recente",
            0,
        )
        self.lbl_top_products = self._build_text_card(
            tables_frame,
            "Top produtos (unidades)",
            1,
        )
        self.lbl_low_stock = self._build_text_card(
            tables_frame,
            "Estoque critico",
            2,
            text_color="#e74c3c",
        )

        ctk.CTkButton(
            self.tab,
            text="Atualizar dashboard",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.refresh_callback,
            height=38,
        ).pack(pady=8)

    def refresh(self):
        try:
            stats = database.get_stats()
        except Exception:
            stats = {}

        products = database.get_products()
        self.lbl_receita.configure(text=f"R$ {stats.get('totalRevenue', 0.0):,.2f}")
        self.lbl_total_prod.configure(text=str(len(products)))
        self.lbl_ticket.configure(text=f"R$ {stats.get('averageTicket', 0.0):,.2f}")
        self.lbl_pedidos_hoje.configure(text=str(stats.get("ordersToday", 0)))
        self.lbl_baixo_estoque.configure(text=str(stats.get("lowStockCount", 0)))
        self.lbl_pedidos_pendentes.configure(text=str(stats.get("pendingOrders", 0)))
        self.lbl_pagos.configure(text=str(stats.get("paidOrders", 0)))
        self.lbl_enviados.configure(text=str(stats.get("shippedOrders", 0)))

        activity = stats.get("recentActivity", [])
        self.lbl_activity.configure(
            text="\n".join(
                f"#{item.get('id', '?')} {item.get('customer', '?')} R${item.get('total', 0):.0f} [{item.get('status', '?')}]"
                for item in activity[:5]
            ) or "Nenhuma atividade ainda."
        )

        top_products = stats.get("topProducts", [])
        self.lbl_top_products.configure(
            text="\n".join(
                f"{index + 1}. {item.get('name', '?')} ({item.get('sales', 0)} un.)"
                for index, item in enumerate(top_products[:5])
            ) or "Sem vendas registradas."
        )

        low_items = stats.get("lowStockItems", [])
        self.lbl_low_stock.configure(
            text="\n".join(
                f"{item.get('name', '?')}: {item.get('stock', 0)} un."
                for item in low_items[:6]
            ) or "Nenhum item critico."
        )

    def _build_kpi_card(self, parent, label, *, color=None, col=0):
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.grid(row=0, column=col, padx=8, pady=4, sticky="ew")
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12)).pack(pady=(14, 2))
        kwargs = {"font": ctk.CTkFont(size=26, weight="bold")}
        if color:
            kwargs["text_color"] = color
        value_label = ctk.CTkLabel(card, text="--", **kwargs)
        value_label.pack(pady=(0, 14))
        return value_label

    def _build_text_card(self, parent, title, column, *, text_color=None):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=column, padx=6, pady=4, sticky="nsew")
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(10, 4))
        label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=220,
            text_color=text_color,
        )
        label.pack(padx=10, pady=(0, 10), anchor=tk.W)
        return label
