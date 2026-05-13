import tkinter as tk
from tkinter import ttk, messagebox
import database
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class SistemaLogisticaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minha Loja - Sistema Local de Vendas e Logística")
        self.root.geometry("1000x700")
        
        # Tentativa de inicializar um tema melhorzinho do Tkinter
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        
        style.configure("TNotebook.Tab", font=("Helvetica", 11, "bold"), padding=[10, 5])
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Card.TFrame", background="#f0f0f0", relief="raised", borderwidth=1)
        
        # Notebook central (Abas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frames (Abas)
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_estoque = ttk.Frame(self.notebook)
        self.tab_pedidos = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_dashboard, text="📊 Dashboard Geral")
        self.notebook.add(self.tab_estoque, text="📦 Estoque & Produtos")
        self.notebook.add(self.tab_pedidos, text="🚚 Logística de Pedidos")
        
        # Constrói o layout interno de cada Aba
        self._setup_dashboard()
        self._setup_estoque()
        self._setup_pedidos()
        
        # Carrega dados do database_mock.py
        self._refresh_all()

        # Inicia servidor de integração em segundo plano
        self._start_api_server()



    def _setup_dashboard(self):
        lbl = ttk.Label(self.tab_dashboard, text="Resumo Dinâmico do E-commerce", style="Header.TLabel")
        lbl.pack(pady=15)
        
        # Frame envolvente dos cards
        frame_cards = ttk.Frame(self.tab_dashboard)
        frame_cards.pack(fill=tk.X, padx=20, pady=20)
        frame_cards.columnconfigure(0, weight=1)
        frame_cards.columnconfigure(1, weight=1)
        frame_cards.columnconfigure(2, weight=1)
        
        # Cards (Frames visuais para estatísticas)
        card1 = ttk.Frame(frame_cards, style="Card.TFrame", padding=20)
        card1.grid(row=0, column=0, padx=10, sticky="ew")
        ttk.Label(card1, text="Total de Produtos", font=("Helvetica", 10)).pack()
        self.lbl_total_prod = ttk.Label(card1, text="0", font=("Helvetica", 18, "bold"))
        self.lbl_total_prod.pack(pady=5)
        
        card2 = ttk.Frame(frame_cards, style="Card.TFrame", padding=20)
        card2.grid(row=0, column=1, padx=10, sticky="ew")
        ttk.Label(card2, text="Itens com Baixo Estoque (<5)", font=("Helvetica", 10)).pack()
        self.lbl_baixo_estoque = ttk.Label(card2, text="0", font=("Helvetica", 18, "bold"), foreground="#e63946")
        self.lbl_baixo_estoque.pack(pady=5)
        
        card3 = ttk.Frame(frame_cards, style="Card.TFrame", padding=20)
        card3.grid(row=0, column=2, padx=10, sticky="ew")
        ttk.Label(card3, text="Pedidos Prontos para Envio", font=("Helvetica", 10)).pack()
        self.lbl_pedidos_pendentes = ttk.Label(card3, text="0", font=("Helvetica", 18, "bold"), foreground="#2a9d8f")
        self.lbl_pedidos_pendentes.pack(pady=5)
        
        btn_refresh = ttk.Button(self.tab_dashboard, text="🔄 Atualizar Dashboard", command=self._refresh_all)
        btn_refresh.pack(pady=30)

    def _setup_estoque(self):
        # Barra superior com botões de ação
        top_frame = ttk.Frame(self.tab_estoque)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="Gestão de Inventário Centralizada", style="Header.TLabel").pack(side=tk.LEFT)
        
        btn_excluir = ttk.Button(top_frame, text="Excluir", command=self._deletar_produto)
        btn_excluir.pack(side=tk.RIGHT, padx=5)

        btn_att_estoque = ttk.Button(top_frame, text="✍️ Modificar Quantidade", command=self._abrir_modal_att_estoque)
        btn_att_estoque.pack(side=tk.RIGHT, padx=5)
        
        btn_novo = ttk.Button(top_frame, text="➕ Adicionar Novo Produto", command=self._abrir_modal_produto)
        btn_novo.pack(side=tk.RIGHT, padx=5)
        
        # Tabela Treeview (Grid de dados)
        columns = ("id", "nome", "categoria", "preco", "estoque")
        self.tree_estoque = ttk.Treeview(self.tab_estoque, columns=columns, show="headings", height=20)
        
        self.tree_estoque.heading("id", text="ID")
        self.tree_estoque.heading("nome", text="Nome do Produto")
        self.tree_estoque.heading("categoria", text="Categoria")
        self.tree_estoque.heading("preco", text="Preço Unit. (R$)")
        self.tree_estoque.heading("estoque", text="Estoque Físico")
        
        # Controle de largura das colunas
        self.tree_estoque.column("id", width=120, anchor=tk.CENTER)
        self.tree_estoque.column("nome", width=350, anchor=tk.W)
        self.tree_estoque.column("categoria", width=150, anchor=tk.CENTER)
        self.tree_estoque.column("preco", width=100, anchor=tk.CENTER)
        self.tree_estoque.column("estoque", width=100, anchor=tk.CENTER)
        
        # Scrollbars na TV
        scroll_y = ttk.Scrollbar(self.tab_estoque, orient=tk.VERTICAL, command=self.tree_estoque.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_estoque.configure(yscrollcommand=scroll_y.set)
        
        self.tree_estoque.pack(fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)

    def _setup_pedidos(self):
        # Topo
        top_frame = ttk.Frame(self.tab_pedidos)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="Controle de Envio E-commerce", style="Header.TLabel").pack(side=tk.LEFT)
        
        btn_enviar = ttk.Button(top_frame, text="✅ Marcar Pedido Selecionado como 'Enviado'", command=self._dispatch_order)
        btn_enviar.pack(side=tk.RIGHT, padx=5)
        
        # Tabela Treeview
        columns = ("id", "cliente", "itens", "total", "status", "data")
        self.tree_pedidos = ttk.Treeview(self.tab_pedidos, columns=columns, show="headings", height=20)
        
        self.tree_pedidos.heading("id", text="Pedido ID")
        self.tree_pedidos.heading("cliente", text="Cliente")
        self.tree_pedidos.heading("itens", text="Detalhes/Itens")
        self.tree_pedidos.heading("total", text="Total Pago")
        self.tree_pedidos.heading("status", text="Status Final")
        self.tree_pedidos.heading("data", text="Data da Compra")
        
        self.tree_pedidos.column("id", width=100, anchor=tk.CENTER)
        self.tree_pedidos.column("cliente", width=200, anchor=tk.W)
        self.tree_pedidos.column("itens", width=300, anchor=tk.W)
        self.tree_pedidos.column("total", width=100, anchor=tk.CENTER)
        self.tree_pedidos.column("status", width=120, anchor=tk.CENTER)
        self.tree_pedidos.column("data", width=140, anchor=tk.CENTER)
        
        scroll_y = ttk.Scrollbar(self.tab_pedidos, orient=tk.VERTICAL, command=self.tree_pedidos.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_pedidos.configure(yscrollcommand=scroll_y.set)
        
        self.tree_pedidos.pack(fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)

    def _refresh_all(self):
        """Função mágica que sincroniza a UI inteira com o DataBase."""
        self._load_products()
        self._load_orders()
        self._update_dashboard()

    def _update_dashboard(self):
        prods = database.get_products()
        total_prod = len(prods)
        baixo_estoque = sum(1 for p in prods if int(p.get("estoque", p.get("stock", 0))) < 5)
        
        orders = database.get_orders()
        # Pedidos 'pagos' ou 'pendente-pagamento' são os que logística deve tratar
        # No Firestore novos pedidos entram como 'pendente'
        pendentes_envio = sum(1 for o in orders if o.get("status", "").lower() in ["pago", "pendente"])
        
        self.lbl_total_prod.config(text=f"{total_prod}")
        self.lbl_baixo_estoque.config(text=f"{baixo_estoque}")
        self.lbl_pedidos_pendentes.config(text=f"{pendentes_envio}")

    def _load_products(self):
        # Limpar tabela local
        for item in self.tree_estoque.get_children():
            self.tree_estoque.delete(item)
            
        prods = database.get_products()
        for p in prods:
            # Suporte a ambos os idiomas para transição suave
            nome = p.get("nome", p.get("name", "Produto"))
            cat = p.get("categoria", p.get("category", "Outros"))
            preco = float(p.get("preco", p.get("price", 0)))
            estoque = int(p.get("estoque", p.get("stock", 0)))
            
            valores = (p["id"], nome, cat, f"R$ {preco:.2f}", estoque)
            row_id = self.tree_estoque.insert("", tk.END, values=valores)
            
            if estoque == 0:
                self.tree_estoque.item(row_id, tags=("zerado",))
            elif estoque < 5:
                self.tree_estoque.item(row_id, tags=("baixo",))

        self.tree_estoque.tag_configure("zerado", background="#ffcccc")
        self.tree_estoque.tag_configure("baixo", background="#fff0b3")

    def _load_orders(self):
        for item in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(item)
            
        orders = database.get_orders()
        # Ordenando para os recentes primeiro
        orders.sort(key=lambda x: x["id"], reverse=True)
        
        for o in orders:
            # Normalização de Pedidos (Firebase vs Mock)
            c_nome = o.get("clienteNome", o.get("customer_name", "Cliente"))
            total = float(o.get("total", 0))
            status = o.get("status", "pendente").lower()
            data_cv = o.get("dataCriacao", o.get("created_at", "--/--"))

            # Formatando itens para visualização rápida
            itens_lista = o.get("itens", o.get("items", []))
            str_items = ", ".join([f"{i.get('quantidade', i.get('quantity', 1))}x {i.get('produtoNome', i.get('product_name', 'Item'))}" for i in itens_lista])
            if len(str_items) > 35: str_items = str_items[:35] + "..."
            
            valores = (o["id"], c_nome, str_items, f"R$ {total:.2f}", status.upper(), data_cv)
            row_id = self.tree_pedidos.insert("", tk.END, values=valores)
            
            if status == "pendente":
                self.tree_pedidos.item(row_id, tags=("pendente",))
            elif status == "pago":
                self.tree_pedidos.item(row_id, tags=("pago",))
            elif status == "enviado":
                self.tree_pedidos.item(row_id, tags=("enviado",))
                
        self.tree_pedidos.tag_configure("pendente", foreground="gray")
        self.tree_pedidos.tag_configure("pago", foreground="#023e8a", font=("Helvetica", 10, "bold"))
        self.tree_pedidos.tag_configure("enviado", foreground="#2a9d8f")

    # =================
    # ACTIONS INTERFACE
    # =================
    def _abrir_modal_produto(self):
        win = tk.Toplevel(self.root)
        win.title("Adicionar Novo Produto")
        win.geometry("450x450")
        win.transient(self.root)
        win.grab_set()

        # Config layout centralizado
        frame_mid = ttk.Frame(win, padding=20)
        frame_mid.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame_mid, text="Nome da Mercadoria:").pack(anchor=tk.W, pady=(0, 2))
        ent_nome = ttk.Entry(frame_mid, width=50)
        ent_nome.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame_mid, text="Categoria do Site:").pack(anchor=tk.W, pady=(0, 2))
        cb_cat = ttk.Combobox(frame_mid, values=["Masculino", "Feminino", "Unissex", "Acessórios", "Promoções"], state="readonly")
        cb_cat.current(0)
        cb_cat.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame_mid, text="Descrição Breve:").pack(anchor=tk.W, pady=(0, 2))
        ent_desc = ttk.Entry(frame_mid, width=50)
        ent_desc.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame_mid, text="Preço de Venda (R$):").pack(anchor=tk.W, pady=(0, 2))
        ent_preco = ttk.Entry(frame_mid, width=20)
        ent_preco.pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(frame_mid, text="Estoque Físico (Qtd):").pack(anchor=tk.W, pady=(0, 2))
        ent_estoque = ttk.Entry(frame_mid, width=20)
        ent_estoque.pack(anchor=tk.W, pady=(0, 20))

        def salvar():
            try:
                n = ent_nome.get().strip()
                c = cb_cat.get()
                d = ent_desc.get().strip()
                p = float(ent_preco.get().replace(",", "."))
                e = int(ent_estoque.get())
                
                if not n or not c:
                    messagebox.showerror("Erro", "Campos nome e categoria são obrigatórios", parent=win)
                    return
                
                database.add_product(n, d, p, e, c)
                messagebox.showinfo("Sucesso", "Produto registrado no inventário e sincronizado virtualmente!", parent=win)
                self._refresh_all()
                win.destroy()
            except ValueError:
                messagebox.showerror("Erro de Formatação", "Preço (ex: 29.90) e Estoque (ex: 5) devem ser números em formatação limpa.", parent=win)

        ttk.Button(frame_mid, text="💾 Salvar e Sincronizar Produto", command=salvar).pack(fill=tk.X, pady=10)


    def _deletar_produto(self):
        selected = self.tree_estoque.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione o produto que deseja deletar do BD.")
            return

        item_id = self.tree_estoque.item(selected[0], "values")[0]
        nome = self.tree_estoque.item(selected[0], "values")[1]

        ans = messagebox.askyesno("Confirmar Exclusão", f"Você quer remover permanentemente da loja o produto:\n\n{nome} (ID: {item_id})\n\nIsso removerá do site também!")
        if ans:
            database.delete_product(item_id)
            self._refresh_all()
            messagebox.showinfo("Produto Removido", f"Produto {nome} excuído.")

    def _abrir_modal_att_estoque(self):
        selected = self.tree_estoque.selection()
        if not selected:
            messagebox.showwarning("Acesso restrito", "Selecione a linha do produto no inventário antes de clicar em alterar.")
            return
        
        item_id = self.tree_estoque.item(selected[0], "values")[0]
        nome = self.tree_estoque.item(selected[0], "values")[1]
        qtd_atual = self.tree_estoque.item(selected[0], "values")[4]
        
        win = tk.Toplevel(self.root)
        win.title("Modificação Parcial de Estoque")
        win.geometry("380x250")
        win.transient(self.root)
        win.grab_set()
        
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Bipagem / Alteração Manual de Lote", style="Header.TLabel").pack(pady=(0, 15))
        ttk.Label(frame, text=f"Produto Mapeado: {nome}").pack(anchor=tk.W)
        ttk.Label(frame, text=f"Volume registrado atualmente: {qtd_atual} un.").pack(anchor=tk.W, pady=(0, 15))
        
        ttk.Label(frame, text="Insira o novo Volume Total no galpão:").pack(anchor=tk.W)
        ent_est = ttk.Entry(frame, width=15)
        ent_est.pack(anchor=tk.W, pady=5)
        ent_est.focus()
        
        def atualizar(*args):
            try:
                val = int(ent_est.get())
                if val < 0: raise ValueError
                database.update_product_stock(item_id, val)
                self._refresh_all()
                win.destroy()
            except ValueError:
                messagebox.showerror("Tipagem inválida", "O banco só aceita números inteiros (0 ou mais) para volume físico.", parent=win)
        
        ent_est.bind('<Return>', atualizar)
        ttk.Button(frame, text="Atualizar Banco de Dados (↵)", command=atualizar).pack(anchor=tk.W, pady=15)

    def _dispatch_order(self):
        selected = self.tree_pedidos.selection()
        if not selected:
            messagebox.showwarning("Fila vazia", "Clique sobre uma Ordem de Pedido na lista para processá-la.")
            return
            
        val = self.tree_pedidos.item(selected[0], "values")
        ord_id = val[0]
        status = val[4]
        
        if status.lower() == "enviado":
            messagebox.showinfo("Fechado", "Essa ORDEM já foi expedida pela transportadora.")
            return
            
        if status.lower() == "pendente":
            ans = messagebox.askyesno("Verificação Crucial", "Atenção Total Logística:\n\nEste pedido aparece como PENDENTE (pagamento ainda sob verificação ou boleto não compensado).\nLiberar mercadoria sem comprovado bancário é risco. \n\nVocê tem certeza Cega que quer despachar esta mercadoria agora?")
            if not ans: return
            
        ans = messagebox.askyesno("Processo de Expedição", f"Deseja bipar o código e transferir a ORDEM de Pedido [{ord_id}] para 'ENVIADO' / Na Entrega do Cliente?")
        if ans:
            database.update_order_status(ord_id, "enviado")
            self._refresh_all()
            messagebox.showinfo("Sistema do Site Atualizado", f"Tudo certo! Logística confirmada. O Site vai atualizar para o cliente ver e a caixa foi liberada.")

    # Modificado para suportar chaves em inglês nas ordens recebidas via POST
    def _start_api_server(self):
        def run_server():
            class OrderHandler(BaseHTTPRequestHandler):
                def do_OPTIONS(self):
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()

                def do_POST(self):
                    if self.path == '/order':
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        order = json.loads(post_data)
                        
                        # Processar o pedido no banco de dados local
                        data = database._read_db()
                        
                        # 1. Validar Estoque antes de processar
                        insufficient_stock = []
                        # Adaptando chaves para o que o front envia (items, product_id, quantity)
                        items_key = 'items' if 'items' in order else 'itens'
                        for item in order.get(items_key, []):
                            prod_id = item.get('product_id') or item.get('produto_id')
                            qty_requested = item.get('quantity') or item.get('quantidade', 0)
                            prod_name = item.get('product_name') or item.get('nome_prod', prod_id)
                            
                            # Encontra produto no "banco"
                            product = next((p for p in data['produtos'] if p['id'] == prod_id), None)
                            if not product or int(product.get('stock', product.get('estoque', 0))) < qty_requested:
                                insufficient_stock.append(prod_name)
                        
                        if insufficient_stock:
                            self.send_response(400)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({
                                "status": "error", 
                                "message": f"Estoque insuficiente para: {', '.join(insufficient_stock)}"
                            }).encode())
                            return

                        # 2. Se estoque OK, decrementa e salva o pedido
                        for item in order.get(items_key, []):
                            prod_id = item.get('product_id') or item.get('produto_id')
                            qty_requested = item.get('quantity') or item.get('quantidade', 0)
                            for p in data['produtos']:
                                if p['id'] == prod_id:
                                    stock_key = 'stock' if 'stock' in p else 'estoque'
                                    p[stock_key] = int(p[stock_key]) - qty_requested
                                    break

                        # Ajusta chaves para padronização interna (se necessário)
                        if 'cliente_nome' in order: order['customer_name'] = order.pop('cliente_nome')
                        if 'cliente_email' in order: order['customer_email'] = order.pop('cliente_email')
                        if 'itens' in order: order['items'] = order.pop('itens')
                        for i in order.get('items', []):
                            if 'produto_id' in i: i['product_id'] = i.pop('produto_id')
                            if 'nome_prod' in i: i['product_name'] = i.pop('nome_prod')
                            if 'quantidade' in i: i['quantity'] = i.pop('quantidade')
                            if 'preco_unit' in i: i['unit_price'] = i.pop('preco_unit')

                        order['id'] = f"ord-{len(data['pedidos']) + 1:03d}"
                        order['status'] = 'pago'
                        from datetime import datetime
                        order['created_at'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        data['pedidos'].append(order)
                        database._write_db(data)
                        
                        # Notificar o app Tkinter (usa after para ser thread-safe)
                        customer_name = order.get('customer_name', 'Cliente')
                        self.server.app_instance.root.after(0, self.server.app_instance._refresh_all)
                        self.server.app_instance.root.after(0, lambda: messagebox.showinfo("Novo Pedido!", f"Um novo pedido de {customer_name} foi recebido e o estoque foi atualizado!"))

                        self.send_response(200)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "success", "order_id": order['id']}).encode())
                    else:
                        self.send_response(404)
                        self.end_headers()

            server_address = ('', 5000)
            httpd = HTTPServer(server_address, OrderHandler)
            httpd.app_instance = self
            print("Servidor de Integração rodando na porta 5000...")
            httpd.serve_forever()

        threading.Thread(target=run_server, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaLogisticaApp(root)
    root.mainloop()
