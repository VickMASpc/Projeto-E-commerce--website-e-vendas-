# Grand Parfum — E-commerce e Sistema de Vendas

Projeto beta de uma operação de perfumaria com vitrine online, sistema local de vendas/estoque e dashboard de análise operacional.

## Visão geral

| Módulo | Tecnologia | Responsabilidade |
| --- | --- | --- |
| `E-commerce/` | HTML, CSS, JavaScript e Firebase Web SDK | Loja online com catálogo, busca, autenticação, favoritos, carrinho, checkout, avaliações e área do cliente. |
| `Sistema de vendas/` | Python, CustomTkinter e API HTTP local | Backoffice para produtos, estoque, pedidos, exportação de catálogo e métricas. |
| `Sistema de análise de vendas/React app/` | React, TypeScript, Vite, Tailwind CSS e Recharts | Dashboard visual para acompanhar indicadores e gráficos de vendas. |

## Funcionalidades principais

### Loja online

- Catálogo de perfumes com filtros por categoria, ofertas e lançamentos.
- Busca por marca, categoria, descrição, notas olfativas e destaques.
- Página de produto com galeria, especificações, notas olfativas, avaliações e produtos relacionados.
- Favoritos com sincronização local e, quando o usuário está autenticado, sincronização na nuvem.
- Carrinho com resumo de compra, frete, validação de dados e limite de quantidade.
- Checkout integrado ao registro de pedidos.
- Autenticação por e-mail/senha e Google.
- Área do cliente com dados de perfil, endereços, histórico de pedidos e lista de desejos.
- Banner promocional com cupom de primeira compra e links para promoções da semana.
- Layout responsivo com menu mobile, navegação por categorias e rodapé institucional.

### Sistema de vendas e estoque

- Cadastro, edição e remoção de produtos.
- Controle de estoque e acompanhamento de pedidos.
- Registro de pedidos enviados pela loja.
- Exportação dos dados do catálogo para manter a vitrine atualizada no modo local/mock.
- Integração opcional com Firebase.
- API local para receber pedidos e disponibilizar métricas operacionais.

### Dashboard de análise

- Painel em React para acompanhar resultados da operação.
- Consumo das métricas disponibilizadas pelo sistema local.
- Visualização de indicadores e gráficos para apoiar a análise de vendas.
- Estado vazio coerente quando a API local está indisponível ou sem dados.

## Arquitetura e integração

O fluxo principal conecta as três partes da aplicação:

1. O cliente navega pela loja em `E-commerce/index.html`, consulta produtos e monta o carrinho.
2. O checkout envia o pedido para a API local iniciada pelo sistema Python.
3. O sistema de vendas registra o pedido, atualiza/consulta dados operacionais e mantém o estoque.
4. O dashboard React consulta as métricas para exibir a análise de vendas.
5. No modo local/mock, o sistema Python pode reexportar `E-commerce/products_live.js` para sincronizar a vitrine com os dados locais.

### Endpoints locais

Com o sistema Python em execução, a API fica disponível em `http://localhost:5000`:

| Endpoint | Função |
| --- | --- |
| `POST /order` | Registra pedidos enviados pela loja. |
| `GET /stats` | Entrega métricas para o dashboard de análise. |

## Como executar

### Pré-requisitos

- Python 3.
- Um servidor estático local, como a extensão Live Server, para abrir a loja.
- Node.js e npm para executar o dashboard React e as verificações JavaScript.
- Dependência opcional `firebase-admin`, caso a base remota Firebase seja utilizada.

### Execução local

1. Para utilizar Firebase no sistema Python, instale a dependência opcional:

   ```bash
   pip install firebase-admin
   ```

2. Inicie o sistema local de vendas e a API:

   ```bash
   python "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
   ```

3. Abra `E-commerce/index.html` com Live Server ou outro servidor estático local.

4. Para iniciar o dashboard, acesse a pasta do app React e execute o servidor de desenvolvimento:

   ```bash
   cd "Sistema de análise de vendas/React app"
   npm install
   npm run dev
   ```

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

Para validar o dashboard React:

```bash
cd "Sistema de análise de vendas/React app"
npm run build
```

## Observações de beta

- O checkout registra pedidos para o fluxo operacional, mas não processa pagamento real.
- Algumas áreas institucionais do rodapé ainda exibem avisos ou atalhos simples.
- As imagens podem utilizar visual padrão quando o produto não possui URL de imagem.
- O dashboard depende do sistema Python em execução para mostrar dados reais.

## Repositório

- [Grand Parfum — Projeto E-commerce, website e vendas](https://github.com/VickMASpc/Projeto-E-commerce--website-e-vendas-)

## Configuração segura do Firebase e da API

> **Atenção:** a chave Firebase que já foi comitada anteriormente deve ser revogada/rotacionada no Google Cloud/Firebase Console. Remover o arquivo do repositório não invalida uma chave que já foi exposta no histórico Git.

O sistema de vendas não precisa de credencial Firebase para rodar em desenvolvimento: quando nenhuma credencial válida é encontrada, ele mantém o modo JSON/mock local usando `Sistema de vendas/db_mock.json`.

Para usar Firebase, mantenha a chave fora do versionamento e configure uma das variáveis abaixo:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/seguro/serviceAccountKey.json"
# ou
export FIREBASE_CREDENTIALS_PATH="/caminho/seguro/serviceAccountKey.json"
```

Há um exemplo sem segredo real em `Sistema de vendas/serviceAccountKey.example.json`. Não copie credenciais reais para arquivos versionados.

### Configuração flexível do servidor

As principais opções podem ser alteradas por variáveis de ambiente, sem mudar código:

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `API_HOST` | vazio / desenvolvimento local | Endereço de bind da API. Use `0.0.0.0` para aceitar conexões da rede local. |
| `API_PORT` | `5000` | Porta HTTP da API. |
| `ALLOWED_ORIGINS` | vazio | Lista separada por vírgulas para CORS. Vazio mantém permissivo em desenvolvimento. |
| `API_TOKEN` | vazio | Token opcional para proteger rotas de escrita. |
| `FRONTEND_EXPORT_ENABLED` | `true` | Habilita/desabilita a exportação local para o frontend. |
| `FIREBASE_CREDENTIALS_PATH` | `Sistema de vendas/serviceAccountKey.json` local não versionado | Caminho para credencial Firebase fora do Git. |

Exemplo para disponibilizar na rede local com CORS restrito e token:

```bash
export API_HOST="0.0.0.0"
export API_PORT="5000"
export ALLOWED_ORIGINS="http://localhost:5173,http://192.168.0.10:5173"
export API_TOKEN="troque-por-um-token-forte"
python "Sistema de vendas/server_headless.py"
```

Com `API_TOKEN` definido, chamadas de escrita devem enviar:

```http
Authorization: Bearer troque-por-um-token-forte
```

### Modo headless da API

Para iniciar somente a API, sem abrir CustomTkinter ou carregar telas da interface gráfica:

```bash
python "Sistema de vendas/server_headless.py"
```

O processo imprime host, porta, URL de health check, modo Firebase/mock e permanece ativo até `Ctrl+C`. O entrypoint desktop antigo continua disponível para uso com interface gráfica.


## Guia operacional

A documentação completa de operação local, rede, launcher, credenciais Firebase, segurança e empacotamento com PyInstaller está em [`docs/operacional.md`](docs/operacional.md).

Resumo rápido:

```bash
python "Sistema de vendas/server_headless.py"
```

Para rede local, configure o servidor com `API_HOST=0.0.0.0`, `API_PORT=5000`, `API_TOKEN`, `ALLOWED_ORIGINS` e, se usar Firebase, `FIREBASE_CREDENTIALS_PATH` apontando para uma chave fora do repositório, por exemplo `%APPDATA%\GrandParfum\serviceAccountKey.json`. Não exponha a porta `5000` diretamente na internet; use token, CORS restrito, HTTPS/proxy ou VPN.

Para gerar executável sem embutir credenciais:

```bash
pyinstaller "Sistema de vendas/pyinstaller_server.spec"
```
