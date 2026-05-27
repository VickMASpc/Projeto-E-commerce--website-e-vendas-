import json
import threading
import tkinter as tk
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from tkinter import messagebox, ttk

import database


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

        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("TNotebook.Tab", font=("Helvetica", 11, "bold"), padding=[12, 7])
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("Header.TLabel", font=("Helvetica", 15, "bold"))
        style.configure("Card.TFrame", background="#f4f1e8", relief="solid", borderwidth=1)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_estoque = ttk.Frame(self.notebook)
        self.tab_pedidos = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_estoque, text="Estoque & Produtos")
        self.notebook.add(self.tab_pedidos, text="Pedidos & Logistica")

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
        ttk.Label(
            self.tab_dashboard,
            text="Resumo operacional do e-commerce",
            style="Header.TLabel",
        ).pack(pady=15)

        frame_cards = ttk.Frame(self.tab_dashboard)
        frame_cards.pack(fill=tk.X, padx=20, pady=20)
        for column in range(3):
            frame_cards.columnconfigure(column, weight=1)

        card1 = ttk.Frame(frame_cards, style="Card.TFrame", padding=20)
        card1.grid(row=0, column=0, padx=10, sticky="ew")
        ttk.Label(card1, text="Total de produtos").pack()
        self.lbl_total_prod = ttk.Label(card1, text="0", font=("Helvetica", 18, "bold"))
        self.lbl_total_prod.pack(pady=5)

        card2 = ttk.Frame(frame_cards, style="Card.TFrame", padding=20)
        card2.grid(row=0, column=1, padx=10, sticky="ew")
        ttk.Label(card2, text="Itens com baixo estoque (<5)").pack()
        self.lbl_baixo_estoque = ttk.Label(
            card2,
            text="0",
            font=("Helvetica", 18, "bold"),
            foreground="#c94242",
        )
        self.lbl_baixo_estoque.pack(pady=5)

        card3 = ttk.Frame(frame_cards, style="Card.TFrame", padding=20)
        card3.grid(row=0, column=2, padx=10, sticky="ew")
        ttk.Label(card3, text="Pedidos prontos para envio").pack()
        self.lbl_pedidos_pendentes = ttk.Label(
            card3,
            text="0",
            font=("Helvetica", 18, "bold"),
            foreground="#1f9254",
        )
        self.lbl_pedidos_pendentes.pack(pady=5)

        ttk.Button(
            self.tab_dashboard,
            text="Atualizar dashboard",
            command=self._refresh_all,
        ).pack(pady=30)

    def _setup_estoque(self):
        top_frame = ttk.Frame(self.tab_estoque)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            top_frame,
            text="Gestao centralizada de inventario e conteudo das paginas de produto",
            style="Header.TLabel",
        ).pack(side=tk.LEFT)

        ttk.Button(top_frame, text="Excluir", command=self._deletar_produto).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Modificar quantidade", command=self._abrir_modal_att_estoque).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Editar detalhes", command=self._editar_produto).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Adicionar novo produto", command=lambda: self._abrir_modal_produto()).pack(side=tk.RIGHT, padx=5)

        columns = ("id", "nome", "categoria", "preco", "estoque")
        self.tree_estoque = ttk.Treeview(self.tab_estoque, columns=columns, show="headings", height=20)

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

        scroll_y = ttk.Scrollbar(self.tab_estoque, orient=tk.VERTICAL, command=self.tree_estoque.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_estoque.configure(yscrollcommand=scroll_y.set)
        self.tree_estoque.pack(fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)

        self.tree_estoque.bind("<Double-1>", lambda _event: self._editar_produto())

    def _setup_pedidos(self):
        top_frame = ttk.Frame(self.tab_pedidos)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            top_frame,
            text="Controle de pedidos e expedicao",
            style="Header.TLabel",
        ).pack(side=tk.LEFT)

        ttk.Button(
            top_frame,
            text="Marcar pedido selecionado como enviado",
            command=self._dispatch_order,
        ).pack(side=tk.RIGHT, padx=5)

        columns = ("id", "cliente", "itens", "total", "status", "data")
        self.tree_pedidos = ttk.Treeview(self.tab_pedidos, columns=columns, show="headings", height=20)

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

        scroll_y = ttk.Scrollbar(self.tab_pedidos, orient=tk.VERTICAL, command=self.tree_pedidos.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_pedidos.configure(yscrollcommand=scroll_y.set)
        self.tree_pedidos.pack(fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)

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

        self.lbl_total_prod.config(text=str(total_prod))
        self.lbl_baixo_estoque.config(text=str(baixo_estoque))
        self.lbl_pedidos_pendentes.config(text=str(pendentes_envio))

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

        self.tree_estoque.tag_configure("zerado", background="#ffd6d6")
        self.tree_estoque.tag_configure("baixo", background="#fff3cc")

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
        self.tree_pedidos.tag_configure("pago", foreground="#0f4c81", font=("Helvetica", 10, "bold"))
        self.tree_pedidos.tag_configure("enviado", foreground="#1f9254")

    def _get_selected_product(self):
        selected = self.tree_estoque.selection()
        if not selected:
            return None

        product_id = self.tree_estoque.item(selected[0], "values")[0]
        return next((product for product in database.get_products() if product["id"] == product_id), None)

    def _abrir_modal_produto(self, product=None):
        is_edit = product is not None
        win = tk.Toplevel(self.root)
        win.title("Editar produto" if is_edit else "Adicionar novo produto")
        win.geometry("700x820")
        win.transient(self.root)
        win.grab_set()

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        form_frame = ttk.Frame(canvas, padding=18)
        window_id = canvas.create_window((0, 0), window=form_frame, anchor="nw")

        form_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width),
        )

        ttk.Label(
            form_frame,
            text="Campos da pagina de produto",
            style="Header.TLabel",
        ).pack(anchor=tk.W, pady=(0, 15))

        widgets = {}
        values = product or {}

        for field in PRODUCT_FIELDS:
            if field["widget"] != "check":
                ttk.Label(form_frame, text=field["label"]).pack(anchor=tk.W, pady=(0, 4))

            if field["widget"] == "entry":
                entry = ttk.Entry(form_frame)
                entry.pack(fill=tk.X, pady=(0, 10))
                entry.insert(0, str(values.get(field["key"], "")))
                widgets[field["key"]] = entry

            elif field["widget"] == "combo":
                combo = ttk.Combobox(form_frame, values=field["values"], state="readonly")
                combo.pack(fill=tk.X, pady=(0, 10))
                selected_value = values.get(field["key"], field["values"][0])
                combo.set(selected_value or field["values"][0])
                widgets[field["key"]] = combo

            elif field["widget"] == "check":
                variable = tk.BooleanVar(value=bool(values.get(field["key"], False)))
                check = ttk.Checkbutton(form_frame, text=field["label"], variable=variable)
                check.pack(anchor=tk.W, pady=(0, 10))
                widgets[field["key"]] = variable
                continue

            else:
                text_widget = tk.Text(form_frame, height=field.get("height", 3), wrap="word")
                text_widget.pack(fill=tk.X, pady=(0, 10))
                raw_value = values.get(field["key"], "")
                if isinstance(raw_value, list):
                    raw_value = "\n".join(raw_value)
                text_widget.insert("1.0", str(raw_value))
                widgets[field["key"]] = text_widget

        def read_field(field):
            widget = widgets[field["key"]]
            if field["widget"] == "entry":
                return widget.get().strip()
            if field["widget"] == "combo":
                return widget.get().strip()
            if field["widget"] == "check":
                return widget.get()
            return widget.get("1.0", "end").strip()

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

        ttk.Button(
            form_frame,
            text="Salvar e sincronizar produto",
            command=save_product,
        ).pack(fill=tk.X, pady=(10, 0))

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

        win = tk.Toplevel(self.root)
        win.title("Atualizar estoque")
        win.geometry("380x240")
        win.transient(self.root)
        win.grab_set()

        frame = ttk.Frame(win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Atualizacao de estoque", style="Header.TLabel").pack(pady=(0, 15))
        ttk.Label(frame, text=f"Produto: {product['name']}").pack(anchor=tk.W)
        ttk.Label(frame, text=f"Estoque atual: {product.get('stock', 0)} unidades").pack(anchor=tk.W, pady=(0, 15))
        ttk.Label(frame, text="Novo estoque").pack(anchor=tk.W)

        entry = ttk.Entry(frame, width=18)
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
        ttk.Button(frame, text="Atualizar estoque", command=update_stock).pack(anchor=tk.W, pady=15)

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
                    self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                    self.send_header("Access-Control-Allow-Headers", "Content-Type")
                    self.end_headers()

                def do_POST(self):
                    if self.path != "/order":
                        self.send_response(404)
                        self.end_headers()
                        return

                    content_length = int(self.headers["Content-Length"])
                    order = json.loads(self.rfile.read(content_length))
                    data = database._read_db()

                    insufficient_stock = []
                    items_key = "items" if "items" in order else "itens"
                    for item in order.get(items_key, []):
                        product_id = item.get("product_id") or item.get("produto_id")
                        quantity = item.get("quantity") or item.get("quantidade", 0)
                        product_name = item.get("product_name") or item.get("nome_prod", product_id)
                        product = next((entry for entry in data["produtos"] if entry["id"] == product_id), None)
                        if not product or int(product.get("stock", 0)) < quantity:
                            insufficient_stock.append(product_name)

                    if insufficient_stock:
                        self.send_response(400)
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "status": "error",
                                    "message": f"Estoque insuficiente para: {', '.join(insufficient_stock)}",
                                }
                            ).encode()
                        )
                        return

                    for item in order.get(items_key, []):
                        product_id = item.get("product_id") or item.get("produto_id")
                        quantity = item.get("quantity") or item.get("quantidade", 0)
                        for product in data["produtos"]:
                            if product["id"] == product_id:
                                product["stock"] = int(product.get("stock", 0)) - quantity
                                break

                    if "cliente_nome" in order:
                        order["customer_name"] = order.pop("cliente_nome")
                    if "cliente_email" in order:
                        order["customer_email"] = order.pop("cliente_email")
                    if "itens" in order:
                        order["items"] = order.pop("itens")

                    for item in order.get("items", []):
                        if "produto_id" in item:
                            item["product_id"] = item.pop("produto_id")
                        if "nome_prod" in item:
                            item["product_name"] = item.pop("nome_prod")
                        if "quantidade" in item:
                            item["quantity"] = item.pop("quantidade")
                        if "preco_unit" in item:
                            item["unit_price"] = item.pop("preco_unit")

                    order["id"] = f"ord-{len(data['pedidos']) + 1:03d}"
                    order["status"] = "pago"
                    order["created_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")

                    data["pedidos"].append(order)
                    database._write_db(data)

                    customer_name = order.get("customer_name", "Cliente")
                    self.server.app_instance.root.after(0, self.server.app_instance._refresh_all)
                    self.server.app_instance.root.after(
                        0,
                        lambda: messagebox.showinfo(
                            "Novo pedido",
                            f"Um novo pedido de {customer_name} foi recebido.",
                        ),
                    )

                    self.send_response(200)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "order_id": order["id"]}).encode())

            server_address = ("", 5000)
            httpd = HTTPServer(server_address, OrderHandler)
            httpd.app_instance = self
            print("Servidor de integracao rodando na porta 5000...")
            httpd.serve_forever()

        threading.Thread(target=run_server, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaLogisticaApp(root)
    root.mainloop()
