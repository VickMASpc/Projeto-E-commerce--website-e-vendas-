import json
import threading
import tkinter as tk
from http.server import BaseHTTPRequestHandler, HTTPServer
from tkinter import messagebox, ttk

import customtkinter as ctk

import database

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

PRODUCT_FIELDS = [
    {"key": "name", "label": "Nome do produto", "widget": "entry", "required": True},
    {"key": "brand", "label": "Marca", "widget": "entry", "required": False},
    {
        "key": "category",
        "label": "Categoria",
        "widget": "combo",
        "required": True,
        "values": ["Masculino", "Feminino", "Unissex", "Nicho", "Acessorios"],
    },
    {"key": "tagline", "label": "Frase curta", "widget": "entry", "required": False},
    {"key": "description", "label": "Descricao curta", "widget": "text", "height": 3, "required": True},
    {"key": "longDescription", "label": "Descricao longa", "widget": "text", "height": 5, "required": False},
    {"key": "price", "label": "Preco atual (R$)", "widget": "entry", "required": True},
    {"key": "oldPrice", "label": "Preco antigo (R$)", "widget": "entry", "required": False},
    {"key": "stock", "label": "Estoque fisico", "widget": "entry", "required": True},
    {"key": "sku", "label": "SKU", "widget": "entry", "required": False},
    {"key": "volume_ml", "label": "Volume", "widget": "entry", "required": False},
    {"key": "concentration", "label": "Concentracao", "widget": "entry", "required": False},
    {"key": "olfactiveFamily", "label": "Familia olfativa", "widget": "entry", "required": False},
    {"key": "occasion", "label": "Melhor ocasiao de uso", "widget": "entry", "required": False},
    {"key": "imageEmoji", "label": "Emoji ou icone", "widget": "entry", "required": False},
    {"key": "image_url", "label": "Imagem principal (URL)", "widget": "entry", "required": False},
    {"key": "images", "label": "Galeria (uma URL por linha)", "widget": "text", "height": 4, "required": False},
    {"key": "topNotes", "label": "Notas de saida", "widget": "text", "height": 3, "required": False},
    {"key": "heartNotes", "label": "Notas de coracao", "widget": "text", "height": 3, "required": False},
    {"key": "baseNotes", "label": "Notas de fundo", "widget": "text", "height": 3, "required": False},
    {"key": "highlights", "label": "Destaques da pagina", "widget": "text", "height": 4, "required": False},
    {"key": "rating", "label": "Nota media", "widget": "entry", "required": False},
    {"key": "reviews", "label": "Quantidade de avaliacoes", "widget": "entry", "required": False},
    {"key": "isSale", "label": "Produto em oferta", "widget": "check", "required": False},
    {"key": "isNew", "label": "Lancamento", "widget": "check", "required": False},
]


class SistemaLogisticaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grand Parfum - Sistema Local de Vendas e Logistica")
        self.root.geometry("1120x760")

        # Configurar estilos de widgets TTK (usados nos Treeviews e afins)
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        is_dark_mode = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2b2b2b" if is_dark_mode else "#ebebeb"
        fg_color = "#ffffff" if is_dark_mode else "#000000"
        header_bg = "#333333" if is_dark_mode else "#d9d9d9"
        header_fg = "#ffffff" if is_dark_mode else "#000000"
        selected_bg = "#1f538d"

        style.configure(
            "Treeview", 
            background=bg_color, 
            foreground=fg_color, 
            fieldbackground=bg_color, 
            rowheight=25, 
            borderwidth=0, 
            font=("Helvetica", 11)
        )
        style.configure(
            "Treeview.Heading", 
            background=header_bg, 
            foreground=header_fg, 
            relief="flat", 
            font=("Helvetica", 12, "bold")
        )
        style.map("Treeview", background=[("selected", selected_bg)])

        # Configurar componentes CustomTkinter
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.notebook.add("Dashboard")
        self.notebook.add("Estoque & Produtos")
        self.notebook.add("Pedidos & Logistica")

        self.tab_dashboard = self.notebook.tab("Dashboard")
        self.tab_estoque = self.notebook.tab("Estoque & Produtos")
        self.tab_pedidos = self.notebook.tab("Pedidos & Logistica")

        self._setup_dashboard()
        self._setup_estoque()
        self._setup_pedidos()
        self._refresh_all()
        self._start_api_server()

        if database.USE_FIREBASE:
            database.listen_to_orders(lambda: self.root.after(0, self._refresh_realtime))

    def _refresh_realtime(self):
        self._refresh_all()

    def _setup_dashboard(self):
        ctk.CTkLabel(
            self.tab_dashboard,
            text="Resumo operacional do e-commerce",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        frame_cards = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        frame_cards.pack(fill=tk.X, padx=20, pady=20)
        
        for column in range(3):
            frame_cards.columnconfigure(column, weight=1)

        # Card 1
        card1 = ctk.CTkFrame(frame_cards, corner_radius=15)
        card1.grid(row=0, column=0, padx=15, sticky="ew")
        ctk.CTkLabel(card1, text="Total de produtos", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.lbl_total_prod = ctk.CTkLabel(card1, text="0", font=ctk.CTkFont(size=32, weight="bold"))
        self.lbl_total_prod.pack(pady=(0, 20))

        # Card 2
        card2 = ctk.CTkFrame(frame_cards, corner_radius=15)
        card2.grid(row=0, column=1, padx=15, sticky="ew")
        ctk.CTkLabel(card2, text="Itens com baixo estoque (<5)", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.lbl_baixo_estoque = ctk.CTkLabel(
            card2, text="0", font=ctk.CTkFont(size=32, weight="bold"), text_color="#ff5e5e"
        )
        self.lbl_baixo_estoque.pack(pady=(0, 20))

        # Card 3
        card3 = ctk.CTkFrame(frame_cards, corner_radius=15)
        card3.grid(row=0, column=2, padx=15, sticky="ew")
        ctk.CTkLabel(card3, text="Pedidos prontos para envio", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.lbl_pedidos_pendentes = ctk.CTkLabel(
            card3, text="0", font=ctk.CTkFont(size=32, weight="bold"), text_color="#2ecc71"
        )
        self.lbl_pedidos_pendentes.pack(pady=(0, 20))

        ctk.CTkButton(
            self.tab_dashboard,
            text="Atualizar dashboard",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._refresh_all,
            height=40
        ).pack(pady=40)

    def _setup_estoque(self):
        top_frame = ctk.CTkFrame(self.tab_estoque, fg_color="transparent")
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 20))

        ctk.CTkLabel(
            top_frame,
            text="Gestao centralizada de inventario e conteudo",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side=tk.LEFT)

        ctk.CTkButton(top_frame, text="Excluir", fg_color="#d63031", hover_color="#ff7675", command=self._deletar_produto).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(top_frame, text="Modificar quantidade", command=self._abrir_modal_att_estoque).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(top_frame, text="Editar detalhes", command=self._editar_produto).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(top_frame, text="Adicionar novo produto", command=lambda: self._abrir_modal_produto()).pack(side=tk.RIGHT, padx=5)

        table_frame = ctk.CTkFrame(self.tab_estoque)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "nome", "categoria", "preco", "estoque")
        self.tree_estoque = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tree_estoque.heading("id", text="ID")
        self.tree_estoque.heading("nome", text="Produto")
        self.tree_estoque.heading("categoria", text="Categoria")
        self.tree_estoque.heading("preco", text="Preco")
        self.tree_estoque.heading("estoque", text="Estoque")

        self.tree_estoque.column("id", width=140, anchor=tk.CENTER)
        self.tree_estoque.column("nome", width=360, anchor=tk.W)
        self.tree_estoque.column("categoria", width=160, anchor=tk.CENTER)
        self.tree_estoque.column("preco", width=120, anchor=tk.CENTER)
        self.tree_estoque.column("estoque", width=110, anchor=tk.CENTER)

        scroll_y = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree_estoque.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_estoque.configure(yscrollcommand=scroll_y.set)
        self.tree_estoque.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_estoque.bind("<Double-1>", lambda _event: self._editar_produto())

    def _setup_pedidos(self):
        top_frame = ctk.CTkFrame(self.tab_pedidos, fg_color="transparent")
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 20))

        ctk.CTkLabel(
            top_frame,
            text="Controle de pedidos e expedicao",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side=tk.LEFT)

        ctk.CTkButton(
            top_frame,
            text="Marcar pedido selecionado como enviado",
            command=self._dispatch_order,
            fg_color="#00b894",
            hover_color="#55efc4"
        ).pack(side=tk.RIGHT, padx=5)

        table_frame = ctk.CTkFrame(self.tab_pedidos)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "cliente", "itens", "total", "status", "data")
        self.tree_pedidos = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tree_pedidos.heading("id", text="Pedido")
        self.tree_pedidos.heading("cliente", text="Cliente")
        self.tree_pedidos.heading("itens", text="Itens")
        self.tree_pedidos.heading("total", text="Total")
        self.tree_pedidos.heading("status", text="Status")
        self.tree_pedidos.heading("data", text="Data")

        self.tree_pedidos.column("id", width=100, anchor=tk.CENTER)
        self.tree_pedidos.column("cliente", width=220, anchor=tk.W)
        self.tree_pedidos.column("itens", width=320, anchor=tk.W)
        self.tree_pedidos.column("total", width=110, anchor=tk.CENTER)
        self.tree_pedidos.column("status", width=120, anchor=tk.CENTER)
        self.tree_pedidos.column("data", width=150, anchor=tk.CENTER)

        scroll_y = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree_pedidos.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_pedidos.configure(yscrollcommand=scroll_y.set)
        self.tree_pedidos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _refresh_all(self):
        self._load_products()
        self._load_orders()
        self._update_dashboard()

    def _update_dashboard(self):
        products = database.get_products()
        total_prod = len(products)
        baixo_estoque = sum(1 for product in products if int(product.get("stock", 0)) < 5)

        orders = database.get_orders()
        pendentes_envio = sum(
            1 for order in orders if order.get("status", "").lower() in {"pago", "pendente"}
        )

        self.lbl_total_prod.configure(text=str(total_prod))
        self.lbl_baixo_estoque.configure(text=str(baixo_estoque))
        self.lbl_pedidos_pendentes.configure(text=str(pendentes_envio))

    def _load_products(self):
        for item in self.tree_estoque.get_children():
            self.tree_estoque.delete(item)

        for product in database.get_products():
            values = (
                product["id"],
                product.get("name", "Produto"),
                product.get("category", "Outros"),
                f"R$ {float(product.get('price', 0)):.2f}",
                int(product.get("stock", 0)),
            )
            row_id = self.tree_estoque.insert("", tk.END, values=values)
            stock = int(product.get("stock", 0))
            if stock == 0:
                self.tree_estoque.item(row_id, tags=("zerado",))
            elif stock < 5:
                self.tree_estoque.item(row_id, tags=("baixo",))

        # Adjust colors for tags based on theme (optional enhancement, here we use strong backgrounds)
        self.tree_estoque.tag_configure("zerado", background="#ff7979", foreground="black")
        self.tree_estoque.tag_configure("baixo", background="#f6e58d", foreground="black")

    def _load_orders(self):
        for item in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(item)

        orders = database.get_orders()
        orders.sort(key=lambda order: order["id"], reverse=True)

        for order in orders:
            customer_name = order.get("clienteNome", order.get("customer_name", "Cliente"))
            total = float(order.get("total", 0))
            status = order.get("status", "pendente").lower()
            created_at = order.get("dataCriacao", order.get("created_at", "--/--"))

            items = order.get("itens", order.get("items", []))
            item_text = ", ".join(
                f"{entry.get('quantidade', entry.get('quantity', 1))}x {entry.get('produtoNome', entry.get('product_name', 'Item'))}"
                for entry in items
            )
            if len(item_text) > 38:
                item_text = item_text[:38] + "..."

            values = (
                order["id"],
                customer_name,
                item_text,
                f"R$ {total:.2f}",
                status.upper(),
                created_at,
            )
            row_id = self.tree_pedidos.insert("", tk.END, values=values)

            if status == "pendente":
                self.tree_pedidos.item(row_id, tags=("pendente",))
            elif status == "pago":
                self.tree_pedidos.item(row_id, tags=("pago",))
            elif status == "enviado":
                self.tree_pedidos.item(row_id, tags=("enviado",))

        self.tree_pedidos.tag_configure("pendente", foreground="gray")
        self.tree_pedidos.tag_configure("pago", foreground="#3498db", font=("Helvetica", 11, "bold"))
        self.tree_pedidos.tag_configure("enviado", foreground="#2ecc71")

    def _get_selected_product(self):
        selected = self.tree_estoque.selection()
        if not selected:
            return None

        product_id = self.tree_estoque.item(selected[0], "values")[0]
        return next((product for product in database.get_products() if product["id"] == product_id), None)

    def _abrir_modal_produto(self, product=None):
        is_edit = product is not None
        win = ctk.CTkToplevel(self.root)
        win.title("Editar produto" if is_edit else "Adicionar novo produto")
        win.geometry("700x820")
        win.transient(self.root)
        win.grab_set()

        form_frame = ctk.CTkScrollableFrame(win)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            form_frame,
            text="Detalhes do Produto",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor=tk.W, pady=(0, 20))

        widgets = {}
        values = product or {}

        for field in PRODUCT_FIELDS:
            if field["widget"] != "check":
                ctk.CTkLabel(form_frame, text=field["label"]).pack(anchor=tk.W, pady=(5, 0))

            if field["widget"] == "entry":
                entry = ctk.CTkEntry(form_frame)
                entry.pack(fill=tk.X, pady=(0, 10))
                entry.insert(0, str(values.get(field["key"], "")))
                widgets[field["key"]] = entry

            elif field["widget"] == "combo":
                combo = ctk.CTkOptionMenu(form_frame, values=field["values"])
                combo.pack(fill=tk.X, pady=(0, 10))
                selected_value = values.get(field["key"], field["values"][0])
                combo.set(selected_value or field["values"][0])
                widgets[field["key"]] = combo

            elif field["widget"] == "check":
                variable = ctk.BooleanVar(value=bool(values.get(field["key"], False)))
                check = ctk.CTkCheckBox(form_frame, text=field["label"], variable=variable)
                check.pack(anchor=tk.W, pady=(10, 10))
                widgets[field["key"]] = variable
                continue

            else:
                height = field.get("height", 3) * 20  # Ajuste aproximado para pixels
                text_widget = ctk.CTkTextbox(form_frame, height=height, wrap="word")
                text_widget.pack(fill=tk.X, pady=(0, 10))
                raw_value = values.get(field["key"], "")
                if isinstance(raw_value, list):
                    raw_value = "\n".join(raw_value)
                text_widget.insert("1.0", str(raw_value))
                widgets[field["key"]] = text_widget

        def read_field(field):
            widget = widgets[field["key"]]
            if field["widget"] in ("entry", "combo"):
                return widget.get().strip()
            if field["widget"] == "check":
                return widget.get()
            return widget.get("1.0", "end-1c").strip()

        def save_product():
            payload = {}
            for field in PRODUCT_FIELDS:
                value = read_field(field)
                if field["required"] and not value:
                    messagebox.showerror(
                        "Campo obrigatorio",
                        f"O campo '{field['label']}' precisa ser preenchido.",
                        parent=win,
                    )
                    return
                payload[field["key"]] = value

            try:
                payload["price"] = float(str(payload.get("price", "0")).replace(",", "."))
                payload["oldPrice"] = float(str(payload.get("oldPrice") or "0").replace(",", "."))
                payload["stock"] = int(float(payload.get("stock", 0)))
                payload["rating"] = float(str(payload.get("rating") or "4.8").replace(",", "."))
                payload["reviews"] = int(float(payload.get("reviews") or 0))
            except ValueError:
                messagebox.showerror(
                    "Dados invalidos",
                    "Preco, preco antigo, estoque, rating e reviews devem ser numericos.",
                    parent=win,
                )
                return

            if is_edit:
                payload["id"] = product["id"]
                saved = database.update_product(product["id"], payload)
                if not saved:
                    messagebox.showerror("Erro", "Nao foi possivel atualizar o produto.", parent=win)
                    return
                messagebox.showinfo("Atualizado", "Produto atualizado e sincronizado.", parent=win)
            else:
                new_id = database.add_product(
                    payload["name"],
                    payload["description"],
                    payload["price"],
                    payload["stock"],
                    payload["category"],
                    payload,
                )
                if not new_id:
                    messagebox.showerror("Erro", "Nao foi possivel salvar o produto.", parent=win)
                    return
                messagebox.showinfo("Sucesso", f"Produto {new_id} registrado com todos os detalhes.", parent=win)

            self._refresh_all()
            win.destroy()

        ctk.CTkButton(
            form_frame,
            text="Salvar e sincronizar produto",
            font=ctk.CTkFont(weight="bold"),
            command=save_product,
            height=40
        ).pack(fill=tk.X, pady=(20, 10))

    def _editar_produto(self):
        product = self._get_selected_product()
        if not product:
            messagebox.showwarning("Selecao", "Selecione um produto para editar.")
            return
        self._abrir_modal_produto(product)

    def _deletar_produto(self):
        product = self._get_selected_product()
        if not product:
            messagebox.showwarning("Atencao", "Selecione o produto que deseja excluir.")
            return

        answer = messagebox.askyesno(
            "Confirmar exclusao",
            f"Remover permanentemente {product['name']} ({product['id']}) do sistema e do site?",
        )
        if answer:
            database.delete_product(product["id"])
            self._refresh_all()
            messagebox.showinfo("Produto removido", f"{product['name']} foi excluido.")

    def _abrir_modal_att_estoque(self):
        product = self._get_selected_product()
        if not product:
            messagebox.showwarning("Acesso restrito", "Selecione um produto antes de alterar o estoque.")
            return

        win = ctk.CTkToplevel(self.root)
        win.title("Atualizar estoque")
        win.geometry("400x260")
        win.transient(self.root)
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Atualizacao de estoque", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 15))
        ctk.CTkLabel(frame, text=f"Produto: {product['name']}").pack(anchor=tk.W)
        ctk.CTkLabel(frame, text=f"Estoque atual: {product.get('stock', 0)} unidades").pack(anchor=tk.W, pady=(0, 15))
        ctk.CTkLabel(frame, text="Novo estoque").pack(anchor=tk.W)

        entry = ctk.CTkEntry(frame, width=200)
        entry.pack(anchor=tk.W, pady=6)
        entry.focus()

        def update_stock(*_args):
            try:
                value = int(float(entry.get()))
                if value < 0:
                    raise ValueError
                database.update_product_stock(product["id"], value)
                self._refresh_all()
                win.destroy()
            except ValueError:
                messagebox.showerror("Tipagem invalida", "Informe um numero inteiro maior ou igual a zero.", parent=win)

        entry.bind("<Return>", update_stock)
        ctk.CTkButton(frame, text="Atualizar estoque", font=ctk.CTkFont(weight="bold"), command=update_stock).pack(anchor=tk.W, pady=15)

    def _dispatch_order(self):
        selected = self.tree_pedidos.selection()
        if not selected:
            messagebox.showwarning("Fila vazia", "Selecione um pedido para processar.")
            return

        values = self.tree_pedidos.item(selected[0], "values")
        order_id = values[0]
        status = values[4].lower()

        if status == "enviado":
            messagebox.showinfo("Pedido finalizado", "Esse pedido ja foi enviado.")
            return

        if status == "pendente":
            confirmed = messagebox.askyesno(
                "Pagamento pendente",
                "Este pedido ainda consta como pendente. Deseja realmente libera-lo para envio?",
            )
            if not confirmed:
                return

        confirmed = messagebox.askyesno(
            "Confirmar envio",
            f"Deseja marcar o pedido {order_id} como enviado?",
        )
        if confirmed:
            database.update_order_status(order_id, "enviado")
            self._refresh_all()
            messagebox.showinfo("Atualizado", "Pedido marcado como enviado.")

    def _start_api_server(self):
        def run_server():
            class OrderHandler(BaseHTTPRequestHandler):
                def do_OPTIONS(self):
                    self.send_response(200)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                    self.send_header("Access-Control-Allow-Headers", "Content-Type")
                    self.end_headers()

                def _send_json(self, status_code, payload):
                    self.send_response(status_code)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

                def do_GET(self):
                    if self.path == "/stats":
                        self._send_json(200, database.get_stats())
                        return

                    if self.path == "/orders":
                        self._send_json(200, {"orders": database.get_orders()})
                        return

                    if self.path == "/products":
                        self._send_json(200, {"products": database.get_products()})
                        return

                    if self.path == "/health":
                        self._send_json(200, {"status": "ok"})
                        return

                    if self.path != "/stats":
                        self._send_json(404, {"status": "error", "message": "Rota nao encontrada."})
                        return

                def do_POST(self):
                    if self.path != "/order":
                        self._send_json(404, {"status": "error", "message": "Rota nao encontrada."})
                        return

                    try:
                        content_length = int(self.headers.get("Content-Length", 0))
                        order = json.loads(self.rfile.read(content_length) or b"{}")
                    except (ValueError, json.JSONDecodeError):
                        self._send_json(400, {"status": "error", "message": "Pedido invalido."})
                        return

                    result = database.create_local_order(order)
                    if not result["ok"]:
                        self._send_json(400, {"status": "error", "message": result["message"]})
                        return

                    customer_name = database.normalize_order(order).get("customer_name", "Cliente")
                    self.server.app_instance.root.after(0, self.server.app_instance._refresh_all)
                    self.server.app_instance.root.after(
                        0,
                        lambda: messagebox.showinfo(
                            "Novo pedido",
                            f"Um novo pedido de {customer_name} foi recebido.",
                        ),
                    )

                    self._send_json(200, {"status": "success", "order_id": result["order_id"]})

            server_address = ("", 5000)
            httpd = HTTPServer(server_address, OrderHandler)
            httpd.app_instance = self
            print("Servidor de integracao rodando na porta 5000...")
            httpd.serve_forever()

        threading.Thread(target=run_server, daemon=True).start()


if __name__ == "__main__":
    root = ctk.CTk()
    app = SistemaLogisticaApp(root)
    root.mainloop()
