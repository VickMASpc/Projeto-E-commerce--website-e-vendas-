# Grand Parfum — E-commerce e Sistema de Vendas

Projeto beta de uma operação de perfumaria com três aplicações integradas: vitrine web, sistema operacional de vendas/estoque e dashboard de métricas.

## Visão geral

| Módulo | Tecnologia | Responsabilidade |
| --- | --- | --- |
| `E-commerce/` | HTML, CSS e JavaScript | Loja estática: catálogo, pesquisa, produto, favoritos e carrinho. |
| `Sistema de vendas/` | Python/Tkinter | Cadastro de produtos, estoque, pedidos, exportação de dados e API local. |
| `Sistema de analise de vendas/` | React/TSX | Dashboard que consome métricas disponibilizadas pelo sistema local. |

## Arquitetura e integração

O fluxo principal do projeto conecta as três partes da aplicação:

1. O usuário navega pela loja em `E-commerce/index.html`, consulta produtos e monta o carrinho.
2. O checkout envia pedidos para a API local iniciada pelo sistema Python.
3. O sistema de vendas registra pedidos, mantém estoque e fornece métricas operacionais.
4. O dashboard React consulta essas métricas para apresentar a análise de vendas.
5. No modo mock, o sistema Python pode reexportar `E-commerce/products_live.js`, mantendo o catálogo estático sincronizado com os dados locais.

### Endpoints locais

Com o sistema Python em execução, a API fica disponível em `http://localhost:5000`:

| Endpoint | Função |
| --- | --- |
| `POST /order` | Registra pedidos enviados pela loja. |
| `GET /stats` | Entrega métricas para o dashboard de análise. |

## Funcionalidades

- Catálogo de perfumes com filtros por categoria, ofertas, lançamentos e favoritos.
- Busca por marca, categoria, descrição, notas olfativas e destaques.
- Página de produto com galeria, especificações, notas e itens relacionados.
- Carrinho com resumo, frete, validação básica de dados e limite por estoque conhecido.
- Favoritos locais para comparação.
- Sistema Python para adicionar, editar e remover produtos, ajustar estoque e acompanhar pedidos.
- Exportação de `products_live.js` para manter a loja estática atualizada quando o modo mock é utilizado.
- Dashboard de análise conectado ao endpoint local de métricas.

## Como executar

### Pré-requisitos

- Python 3.
- Um servidor estático local, como a extensão Live Server, para abrir a loja.
- Node.js somente para as verificações de sintaxe JavaScript descritas abaixo.
- Dependência opcional `firebase-admin`, caso a base remota Firebase seja utilizada.

### Execução local

1. Para utilizar Firebase, instale a dependência opcional:

   ```bash
   pip install firebase-admin
   ```

2. Inicie o sistema local de vendas e a API:

   ```bash
   python "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
   ```

3. Abra `E-commerce/index.html` com Live Server ou outro servidor estático local.

4. Inicie o dashboard em `Sistema de analise de vendas/` conforme o fluxo de desenvolvimento React configurado nesse módulo, mantendo o sistema Python ativo para obter métricas reais.

## Understand Anything aplicado ao projeto

Este repositório foi preparado para análise com o projeto open source [Understand Anything](https://github.com/Lum1104/Understand-Anything), uma ferramenta que examina uma base de código e produz uma representação navegável de arquivos, funções, classes, dependências e fluxos de negócio.

### Objetivo da análise neste e-commerce

A análise é útil neste projeto porque a aplicação é dividida entre tecnologias e responsabilidades diferentes. O grafo gerado pelo Understand Anything deve permitir:

- visualizar a relação entre a loja JavaScript, o backend local Python e o dashboard React/TSX;
- identificar arquivos e funções envolvidos no fluxo de pedido, estoque, exportação do catálogo e métricas;
- facilitar onboarding e manutenção sem exigir leitura manual inicial de todos os módulos;
- apoiar a avaliação de impacto ao modificar integrações, dados ou regras de negócio.

### Evidências versionadas no repositório

A execução/preparação do Understand Anything é registrada no diretório `.understand-anything/`, atualmente composto por:

```text
.understand-anything/
├── .understandignore
├── intermediate/
└── tmp/
```

O arquivo `.understand-anything/.understandignore` está configurado para ignorar o próprio diretório `.understand-anything/` durante a varredura:

```gitignore
.understand-anything/
```

Essa regra impede que arquivos produzidos pela análise sejam analisados novamente como se fossem código-fonte do Grand Parfum, evitando ruído e referências circulares no processamento.

### Estado atual dos artefatos

O repositório contém a estrutura de trabalho do Understand Anything (`.understandignore`, `intermediate/` e `tmp/`). Entretanto, **não há um arquivo `.understand-anything/knowledge-graph.json` versionado na raiz desse diretório** no estado atual da branch `main`.

No fluxo documentado pela própria ferramenta, `knowledge-graph.json` é o artefato final que alimenta o dashboard interativo e pode ser compartilhado com a equipe. Portanto, a presença atual de `.understand-anything/` demonstra a preparação/execução da análise, mas o grafo final publicável ainda precisa ser gerado ou adicionado ao repositório para permitir exploração direta por outros colaboradores.

### Como gerar ou atualizar a análise

A documentação do Understand Anything fornece o seguinte fluxo principal, executado em uma plataforma compatível após a instalação do plugin/ferramenta:

```bash
# Analisa o código e cria/atualiza o grafo
/understand

# Abre o dashboard interativo do grafo
/understand-dashboard

# Consulta o código analisado em linguagem natural
/understand-chat Como o fluxo de pedido conecta a loja ao sistema de vendas?

# Analisa impacto das alterações locais
/understand-diff

# Produz uma visão de domínios e fluxos de negócio
/understand-domain

# Cria material de onboarding baseado no grafo
/understand-onboard
```

Para este projeto, perguntas relevantes após a geração do grafo incluem:

```text
Como o POST /order é acionado a partir do checkout?
Como o estoque limita itens disponíveis no carrinho?
Como products_live.js é exportado e utilizado pela loja?
Como GET /stats alimenta o dashboard de análise de vendas?
Quais arquivos seriam afetados por uma alteração no formato de produto?
```

### Conteúdo que deve ser analisado

A análise deve cobrir os três módulos funcionais do repositório:

| Escopo | O que observar no grafo |
| --- | --- |
| `E-commerce/` | Catálogo, busca, página de produto, carrinho, favoritos, checkout e consumo dos dados exportados. |
| `Sistema de vendas/` | Persistência, integração opcional com Firebase, gerenciamento de estoque, registro de pedidos, exportação e endpoints locais. |
| `Sistema de analise de vendas/` | Componentes do dashboard e consumo das métricas do endpoint `/stats`. |

A pasta `.understand-anything/` não deve ser analisada como código da aplicação, conforme a regra já presente em `.understandignore`.

### Artefatos recomendados para compartilhamento

Após uma execução completa, o Understand Anything recomenda versionar os artefatos de análise úteis à equipe e manter fora do compartilhamento arquivos transitórios. Para este projeto, a organização esperada é:

```text
.understand-anything/
├── .understandignore
├── knowledge-graph.json       # grafo final compartilhável, após ser gerado
├── intermediate/              # processamento intermediário/local
└── tmp/                       # temporários locais
```

Conforme a orientação da ferramenta, `intermediate/` e arquivos temporários não são o produto final da documentação; o arquivo de grafo é o elemento central para navegação, dashboard e reaproveitamento por colaboradores.

### Manutenção da documentação de arquitetura

Quando funcionalidades importantes forem adicionadas — por exemplo, pagamento real, novos endpoints, autenticação, mudanças no estoque ou novas métricas — recomenda-se:

1. atualizar e testar o código;
2. executar novamente `/understand` para refletir as novas dependências no grafo;
3. revisar o dashboard com `/understand-dashboard`;
4. adicionar/atualizar o artefato compartilhável do grafo, caso a equipe opte por versioná-lo;
5. manter esta seção alinhada ao estado real do repositório.

## Verificação sem navegador

Use estes comandos para validar a sintaxe e os dados principais:

```bash
node --check "E-commerce/app.js"
node --check "E-commerce/products_live.js"
python -m py_compile "Sistema de vendas/database.py" "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
```

Para reexportar os dados mock para a loja:

```bash
python -c "import sys; sys.path.insert(0, 'Sistema de vendas'); import database; database.USE_FIREBASE=False; data=database._read_db(); database._write_db(data)"
```

## Observações de beta

- O checkout registra pedidos para o fluxo operacional, mas não processa pagamento real.
- Algumas áreas institucionais do rodapé ainda exibem avisos ou atalhos simples.
- As imagens podem utilizar visual padrão quando o produto não possui URL de imagem.
- O dashboard depende do sistema Python em execução para mostrar dados reais; quando indisponível, exibe estado vazio coerente.

## Referências

- [Understand Anything — repositório oficial](https://github.com/Lum1104/Understand-Anything)
- [Grand Parfum — repositório deste projeto](https://github.com/VickMASpc/Projeto-E-commerce--website-e-vendas-)
