"""Products and inventory UI for the CustomTkinter shell."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import config
import database
from domain.product import validate_product
from ui.components import (
    build_error_box,
    build_labeled_entry,
    build_labeled_optionmenu,
    build_labeled_textbox,
    build_section,
    build_treeview_with_scrollbar,
    set_error_text,
)

PRODUCT_CATEGORIES = ["Masculino", "Feminino", "Unissex", "Nicho", "Acessorios"]

PRODUCT_FORM_SECTIONS = [
    {
        "title": "Basic",
        "description": "Core catalog information shown in the product list and export.",
        "fields": [
            {"key": "name", "label": "Nome do produto", "widget": "entry", "required": True},
            {"key": "brand", "label": "Marca", "widget": "entry", "required": False},
            {
                "key": "category",
                "label": "Categoria",
                "widget": "combo",
                "required": True,
                "values": PRODUCT_CATEGORIES,
            },
            {"key": "sku", "label": "SKU", "widget": "entry", "required": False},
            {"key": "tagline", "label": "Frase curta", "widget": "entry", "required": False},
            {"key": "description", "label": "Descricao curta", "widget": "text", "height": 70, "required": True},
            {"key": "longDescription", "label": "Descricao longa", "widget": "text", "height": 110, "required": False},
        ],
    },
    {
        "title": "Pricing/Stock",
        "description": "Commercial and availability fields used by inventory and export flows.",
        "fields": [
            {"key": "price", "label": "Preco atual (R$)", "widget": "entry", "required": True},
            {"key": "oldPrice", "label": "Preco antigo (R$)", "widget": "entry", "required": False},
            {"key": "stock", "label": "Estoque fisico", "widget": "entry", "required": True},
            {"key": "rating", "label": "Nota media", "widget": "entry", "required": False},
            {"key": "reviews", "label": "Quantidade de avaliacoes", "widget": "entry", "required": False},
            {"key": "isSale", "label": "Produto em oferta", "widget": "check", "required": False},
            {"key": "isNew", "label": "Lancamento", "widget": "check", "required": False},
        ],
    },
    {
        "title": "Fragrance Details",
        "description": "Perfume-specific details kept compatible with the existing product payload.",
        "fields": [
            {"key": "volume_ml", "label": "Volume", "widget": "entry", "required": False},
            {"key": "concentration", "label": "Concentracao", "widget": "entry", "required": False},
            {"key": "olfactiveFamily", "label": "Familia olfativa", "widget": "entry", "required": False},
            {"key": "occasion", "label": "Melhor ocasiao de uso", "widget": "entry", "required": False},
            {"key": "topNotes", "label": "Notas de saida", "widget": "text", "height": 70, "required": False},
            {"key": "heartNotes", "label": "Notas de coracao", "widget": "text", "height": 70, "required": False},
            {"key": "baseNotes", "label": "Notas de fundo", "widget": "text", "height": 70, "required": False},
            {"key": "highlights", "label": "Destaques da pagina", "widget": "text", "height": 90, "required": False},
        ],
    },
    {
        "title": "Images/Metadata",
        "description": "Media references and secondary merchandising metadata.",
        "fields": [
            {"key": "imageEmoji", "label": "Emoji ou icone", "widget": "entry", "required": False},
            {"key": "image_url", "label": "Imagem principal (URL)", "widget": "entry", "required": False},
            {"key": "images", "label": "Galeria (uma URL por linha)", "widget": "text", "height": 90, "required": False},
        ],
    },
]


class ProductsInventoryView:
    def __init__(self, root, tab, refresh_callback):
        self.root = root
        self.tab = tab
        self.refresh_callback = refresh_callback
        self.tree = None
        self.search_var = ctk.StringVar(value="")
        self.category_var = ctk.StringVar(value="Todas")
        self.low_stock_var = ctk.BooleanVar(value=False)
        self.out_of_stock_var = ctk.BooleanVar(value=False)
        self.sale_var = ctk.BooleanVar(value=False)
        self.new_var = ctk.BooleanVar(value=False)

    def build(self):
        top_frame = ctk.CTkFrame(self.tab, fg_color="transparent")
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 12))

        ctk.CTkLabel(
            top_frame,
            text="Gestao centralizada de inventario e conteudo",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side=tk.LEFT)

        ctk.CTkButton(
            top_frame,
            text="Excluir",
            fg_color="#d63031",
            hover_color="#ff7675",
            command=self.delete_selected_product,
        ).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(
            top_frame,
            text="Modificar quantidade",
            command=self.open_stock_adjustment_modal,
        ).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(
            top_frame,
            text="Editar detalhes",
            command=self.edit_selected_product,
        ).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(
            top_frame,
            text="Adicionar novo produto",
            command=lambda: self.open_product_modal(),
        ).pack(side=tk.RIGHT, padx=5)

        filters_frame = ctk.CTkFrame(self.tab)
        filters_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        filters_frame.grid_columnconfigure(0, weight=3)
        filters_frame.grid_columnconfigure(1, weight=2)
        filters_frame.grid_columnconfigure(2, weight=2)
        filters_frame.grid_columnconfigure(3, weight=2)

        ctk.CTkLabel(filters_frame, text="Busca").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        search_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self.search_var,
            placeholder_text="Buscar por nome, marca ou SKU",
        )
        search_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        search_entry.bind("<KeyRelease>", lambda _event: self.load_products())

        ctk.CTkLabel(filters_frame, text="Categoria").grid(row=0, column=1, sticky="w", padx=12, pady=(12, 0))
        category_menu = ctk.CTkOptionMenu(
            filters_frame,
            values=["Todas", *PRODUCT_CATEGORIES],
            variable=self.category_var,
            command=lambda _value: self.load_products(),
        )
        category_menu.grid(row=1, column=1, sticky="ew", padx=12, pady=(0, 12))

        toggles = ctk.CTkFrame(filters_frame, fg_color="transparent")
        toggles.grid(row=0, column=2, columnspan=2, rowspan=2, sticky="e", padx=12, pady=12)

        for text, variable in (
            ("Baixo estoque", self.low_stock_var),
            ("Sem estoque", self.out_of_stock_var),
            ("Em oferta", self.sale_var),
            ("Lancamento", self.new_var),
        ):
            ctk.CTkCheckBox(
                toggles,
                text=text,
                variable=variable,
                command=self.load_products,
            ).pack(side=tk.LEFT, padx=(0, 10))

        table_frame = ctk.CTkFrame(self.tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "name", "brand", "category", "sku", "price", "stock", "flags")
        self.tree, scrollbar = build_treeview_with_scrollbar(table_frame, columns)

        headings = {
            "id": ("ID", 140, tk.CENTER),
            "name": ("Name", 230, tk.W),
            "brand": ("Brand", 150, tk.W),
            "category": ("Category", 130, tk.CENTER),
            "sku": ("SKU", 130, tk.CENTER),
            "price": ("Price", 100, tk.CENTER),
            "stock": ("Stock", 80, tk.CENTER),
            "flags": ("Flags", 110, tk.CENTER),
        }
        for column, (label, width, anchor) in headings.items():
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected_product())

    def _filtered_products(self):
        products = database.get_products()
        query = self.search_var.get().strip().lower()
        category = self.category_var.get().strip()

        def matches(product):
            if query:
                haystack = " ".join(
                    str(product.get(field, "") or "")
                    for field in ("name", "brand", "sku")
                ).lower()
                if query not in haystack:
                    return False

            if category and category != "Todas" and str(product.get("category", "") or "") != category:
                return False

            stock = int(product.get("stock", 0))
            if self.low_stock_var.get() and stock >= config.LOW_STOCK_THRESHOLD:
                return False
            if self.out_of_stock_var.get() and stock != 0:
                return False
            if self.sale_var.get() and not bool(product.get("isSale")):
                return False
            if self.new_var.get() and not bool(product.get("isNew")):
                return False
            return True

        return [product for product in products if matches(product)]

    def load_products(self):
        if not self.tree:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for product in self._filtered_products():
            stock = int(product.get("stock", 0))
            flags = []
            if bool(product.get("isSale")):
                flags.append("SALE")
            if bool(product.get("isNew")):
                flags.append("NEW")
            if stock == 0:
                flags.append("OUT")
            elif stock < config.LOW_STOCK_THRESHOLD:
                flags.append("LOW")

            values = (
                product["id"],
                product.get("name", "Produto"),
                product.get("brand", ""),
                product.get("category", "Outros"),
                product.get("sku", ""),
                f"R$ {float(product.get('price', 0)):.2f}",
                stock,
                " | ".join(flags) if flags else "-",
            )
            row_id = self.tree.insert("", tk.END, values=values)
            if stock == 0:
                self.tree.item(row_id, tags=("zerado",))
            elif stock < config.LOW_STOCK_THRESHOLD:
                self.tree.item(row_id, tags=("baixo",))

        self.tree.tag_configure("zerado", background="#ff7979", foreground="black")
        self.tree.tag_configure("baixo", background="#f6e58d", foreground="black")

    def get_selected_product(self):
        if not self.tree:
            return None
        selected = self.tree.selection()
        if not selected:
            return None

        product_id = self.tree.item(selected[0], "values")[0]
        return next((product for product in database.get_products() if product["id"] == product_id), None)

    def open_product_modal(self, product=None):
        is_edit = product is not None
        win = ctk.CTkToplevel(self.root)
        win.title("Editar produto" if is_edit else "Adicionar novo produto")
        win.geometry("780x840")
        win.transient(self.root)
        win.grab_set()

        form_frame = ctk.CTkScrollableFrame(win)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            form_frame,
            text="Detalhes do Produto",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor=tk.W, pady=(0, 8))
        ctk.CTkLabel(
            form_frame,
            text="Todos os campos existentes do produto sao preservados e validados antes de salvar.",
            text_color=("gray40", "gray70"),
        ).pack(anchor=tk.W, pady=(0, 12))

        error_label = build_error_box(form_frame)
        widgets = {}
        values = dict(product or {})

        for section in PRODUCT_FORM_SECTIONS:
            body = build_section(form_frame, section["title"], section["description"])
            for field in section["fields"]:
                key = field["key"]
                raw_value = values.get(key, "")
                if isinstance(raw_value, list):
                    raw_value = "\n".join(str(item) for item in raw_value)

                if field["widget"] == "entry":
                    widgets[key] = build_labeled_entry(body, field["label"], str(raw_value))
                elif field["widget"] == "combo":
                    widgets[key] = build_labeled_optionmenu(
                        body,
                        field["label"],
                        field["values"],
                        str(raw_value or field["values"][0]),
                    )
                elif field["widget"] == "check":
                    variable = ctk.BooleanVar(value=bool(raw_value))
                    ctk.CTkCheckBox(body, text=field["label"], variable=variable).pack(anchor=tk.W, pady=(4, 10))
                    widgets[key] = variable
                else:
                    widgets[key] = build_labeled_textbox(
                        body,
                        field["label"],
                        str(raw_value),
                        height=field.get("height", 80),
                    )

        def read_field(field):
            widget = widgets[field["key"]]
            if field["widget"] in ("entry", "combo"):
                return widget.get().strip()
            if field["widget"] == "check":
                return widget.get()
            return widget.get("1.0", "end-1c").strip()

        def validation_message(errors):
            lines = []
            labels = {
                field["key"]: field["label"]
                for section in PRODUCT_FORM_SECTIONS
                for field in section["fields"]
            }
            for key, entries in errors.items():
                field_label = labels.get(key, key)
                joined = "; ".join(entry.get("message", "Invalid value.") for entry in entries)
                lines.append(f"{field_label}: {joined}")
            return "\n".join(lines)

        def save_product():
            set_error_text(error_label, "")
            payload = {}
            raw_payload = {}

            for section in PRODUCT_FORM_SECTIONS:
                for field in section["fields"]:
                    value = read_field(field)
                    payload[field["key"]] = value
                    raw_payload[field["key"]] = value
                    if field["required"] and (value is None or str(value).strip() == ""):
                        set_error_text(error_label, f"O campo '{field['label']}' precisa ser preenchido.")
                        return

            normalized = validate_product(payload, raw_payload)
            if not normalized["valid"]:
                set_error_text(error_label, validation_message(normalized["errors"]))
                return

            product_payload = normalized["product"]
            if is_edit:
                product_payload["id"] = product["id"]
                saved = database.update_product(product["id"], product_payload)
                if not saved:
                    set_error_text(error_label, "Nao foi possivel atualizar o produto.")
                    return
                messagebox.showinfo("Atualizado", "Produto atualizado e sincronizado.", parent=win)
            else:
                new_id = database.add_product(
                    product_payload["name"],
                    product_payload["description"],
                    product_payload["price"],
                    product_payload["stock"],
                    product_payload["category"],
                    product_payload,
                )
                if not new_id:
                    set_error_text(error_label, "Nao foi possivel salvar o produto.")
                    return
                messagebox.showinfo(
                    "Sucesso",
                    f"Produto {new_id} registrado com todos os detalhes.",
                    parent=win,
                )

            self.refresh_callback()
            win.destroy()

        ctk.CTkButton(
            form_frame,
            text="Salvar e sincronizar produto",
            font=ctk.CTkFont(weight="bold"),
            command=save_product,
            height=40,
        ).pack(fill=tk.X, pady=(10, 10))

    def edit_selected_product(self):
        product = self.get_selected_product()
        if not product:
            messagebox.showwarning("Selecao", "Selecione um produto para editar.")
            return
        self.open_product_modal(product)

    def delete_selected_product(self):
        product = self.get_selected_product()
        if not product:
            messagebox.showwarning("Atencao", "Selecione o produto que deseja excluir.")
            return

        answer = messagebox.askyesno(
            "Confirmar exclusao",
            f"Remover permanentemente {product['name']} ({product['id']}) do sistema e do site?",
        )
        if answer:
            database.delete_product(product["id"])
            self.refresh_callback()
            messagebox.showinfo("Produto removido", f"{product['name']} foi excluido.")

    def open_stock_adjustment_modal(self):
        product = self.get_selected_product()
        if not product:
            messagebox.showwarning("Acesso restrito", "Selecione um produto antes de alterar o estoque.")
            return

        win = ctk.CTkToplevel(self.root)
        win.title("Atualizar estoque")
        win.geometry("420x290")
        win.transient(self.root)
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Atualizacao de estoque",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(0, 15))
        ctk.CTkLabel(frame, text=f"Produto: {product['name']}").pack(anchor=tk.W)
        ctk.CTkLabel(frame, text=f"Estoque atual: {product.get('stock', 0)} unidades").pack(anchor=tk.W, pady=(0, 15))
        ctk.CTkLabel(frame, text="Novo estoque").pack(anchor=tk.W)

        error_label = build_error_box(frame)
        entry = ctk.CTkEntry(frame, width=220)
        entry.pack(anchor=tk.W, pady=6)
        entry.insert(0, str(product.get("stock", 0)))
        entry.focus()

        def update_stock(*_args):
            set_error_text(error_label, "")
            try:
                new_value = int(float(entry.get()))
                if new_value < 0:
                    raise ValueError
            except ValueError:
                set_error_text(error_label, "Informe um numero inteiro maior ou igual a zero.")
                return

            current_stock = int(product.get("stock", 0))
            delta = new_value - current_stock
            if delta != 0:
                database.adjust_inventory_stock(
                    product["id"],
                    delta,
                    "Atualizacao manual via painel",
                    note=f"De {current_stock} para {new_value}",
                )

            self.refresh_callback()
            win.destroy()

        entry.bind("<Return>", update_stock)
        ctk.CTkButton(
            frame,
            text="Atualizar estoque",
            font=ctk.CTkFont(weight="bold"),
            command=update_stock,
        ).pack(anchor=tk.W, pady=15)
