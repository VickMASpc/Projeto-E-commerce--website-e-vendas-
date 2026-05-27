# Grand Parfum - E-commerce e Sistema de Vendas

Projeto beta com tres partes integradas:

- `E-commerce/`: loja estatica em HTML, CSS e JavaScript.
- `Sistema de vendas/`: aplicativo local em Python/Tkinter para produtos, estoque, pedidos e exportacao de dados.
- `Sistema de analise de vendas/`: dashboard React/TSX que consome metricas do servidor local.

## Como rodar

1. Instale a dependencia opcional do Firebase, se for usar a base remota:

```bash
pip install firebase-admin
```

2. Inicie o sistema local de vendas:

```bash
python "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
```

3. Abra `E-commerce/index.html` com Live Server ou outro servidor estatico local.

O sistema Python tambem inicia uma API local em `http://localhost:5000`:

- `POST /order`: registra pedidos enviados pela loja.
- `GET /stats`: entrega metricas para o dashboard de analise.

## Funcionalidades

- Catalogo de perfumes com filtros por categoria, ofertas, lancamentos e favoritos.
- Busca por marca, categoria, descricao, notas olfativas e destaques.
- Pagina de produto com galeria, especificacoes, notas e itens relacionados.
- Carrinho com resumo, frete, validacao basica de dados e limite por estoque conhecido.
- Favoritos locais para comparacao.
- Sistema Python para adicionar, editar, remover produtos, ajustar estoque e acompanhar pedidos.
- Exportacao de `products_live.js` para manter a loja estatica atualizada quando o modo mock e usado.
- Dashboard de analise conectado ao endpoint local de metricas.

## Observacoes de beta

- O checkout registra pedidos para o fluxo operacional, mas nao processa pagamento real.
- Algumas areas institucionais do rodape ainda exibem avisos ou atalhos simples.
- As imagens podem usar visual padrao quando o produto nao tiver URL de imagem.
- O dashboard depende do sistema Python em execucao para mostrar dados reais; quando indisponivel, exibe estado vazio coerente.

## Verificacao sem navegador

Use estes comandos para validar sintaxe e dados principais:

```bash
node --check "E-commerce/app.js"
node --check "E-commerce/products_live.js"
python -m py_compile "Sistema de vendas/database.py" "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
```

Para reexportar os dados mock para a loja:

```bash
python -c "import sys; sys.path.insert(0, 'Sistema de vendas'); import database; database.USE_FIREBASE=False; data=database._read_db(); database._write_db(data)"
```
