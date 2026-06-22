# Grand Parfum — E-commerce e Sistema de Vendas

Projeto beta de uma operação de perfumaria com três partes integradas:

| Módulo | Pasta | Função |
| --- | --- | --- |
| Loja online | `E-commerce/` | Catálogo, carrinho, checkout, cupons e envio de pedidos. |
| Sistema de vendas | `Sistema de vendas/` | Backoffice desktop, estoque, pedidos, API HTTP e integração opcional com Firebase. |
| Dashboard | `Sistema de análise de vendas/React app/` | Painel React para métricas, pedidos e produtos. |

## Inicialização rápida

Para rodar em desenvolvimento local, você não precisa de chave Firebase. Se nenhuma credencial for configurada, o sistema usa `Sistema de vendas/db_mock.json`.

### 1. Iniciar o sistema de vendas

Escolha um dos modos abaixo.

#### Opção A — Desktop com interface

Use quando quiser abrir o backoffice com janelas CustomTkinter:

```bash
python "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
```

Esse modo também inicia a API local na porta `5000`.

#### Opção B — Servidor headless, sem interface

Use quando quiser apenas ligar a API para a loja e o dashboard:

```bash
python "Sistema de vendas/server_headless.py"
```

Teste se a API subiu:

```bash
curl http://localhost:5000/health
```

Resposta esperada:

```json
{"status":"ok"}
```

### 2. Acesso à Produção e Loja Pública

A loja de E-commerce em produção não utiliza `localhost` nem `localStorage` para tokens. Ela utiliza a hospedagem no **GitHub Pages** e conecta-se via Web Config ao **Firebase**, utilizando **Cloud Functions** e **App Check** na nuvem para fechar os pedidos de sua empresa de forma segura e global.
Jamais insira chaves reais como token num arquivo frontend público, pois arquivos da web em Javascript estão expostos ao serem lidos via F12, portanto, a segurança autêntica ocorre no lado Cloud com suas Regras.

Para detalhes do deploy online, chaves na nuvem e o Checklist da Operação Produtiva, veja:
🔗 [Guia de Deploy Firebase / GitHub Pages](docs/producao-github-pages-firebase.md)

### 3. Abrir a loja e testar Local (Mock Frontend)

Em desenvolvimento e validação visual de código offline, você pode abrir e testar temporariamente:
Abra `E-commerce/index.html` com um servidor estático local, por exemplo Live Server no VS Code.

> Lembre-se, o modo local JSON/Mock são apenas sandboxes para testes offline interno da tela. Pedidos reais e integrações válidas dependem do ambiente com `Firebase` verdadeiro rodando com as Cloud Functions.

### 3. Rodar o dashboard

```bash
cd "Sistema de análise de vendas/React app"
npm install
npm run dev
```

Para usar uma API remota, crie `Sistema de análise de vendas/React app/.env` com base em `.env.example`:

```bash
VITE_STATS_API_URL=http://192.168.0.10:5000/stats
VITE_API_TOKEN=troque-este-token
```

## Rodar na rede local

No computador que será o servidor, inicie a API aceitando conexões da rede.

### Bash/Linux/macOS

```bash
export API_HOST="0.0.0.0"
export API_PORT="5000"
export API_TOKEN="troque-este-token"
export ALLOWED_ORIGINS="http://localhost:5500,http://192.168.0.10:5173"
python "Sistema de vendas/server_headless.py"
```

### Windows PowerShell

```powershell
$env:API_HOST="0.0.0.0"
$env:API_PORT="5000"
$env:API_TOKEN="troque-este-token"
$env:ALLOWED_ORIGINS="http://localhost:5500,http://192.168.0.10:5173"
python "Sistema de vendas/server_headless.py"
```

Depois, em outro computador da mesma rede, teste:

```bash
curl http://IP_DO_SERVIDOR:5000/health
```

Se não responder, verifique o IP do servidor e libere a porta `5000` no firewall local.

## Usar o launcher no Windows

Na pasta `Sistema de vendas/`, use:

```text
LIGAR_SERVIDOR.bat
```

Você pode arrastar sobre o `.bat`:

- um `server_config.json`, para configurar host, porta, token, CORS e caminho da credencial;
- um `serviceAccountKey.json`, para copiar a credencial Firebase para fora do repositório e iniciar o servidor.

Exemplo seguro de `server_config.json`:

```json
{
  "host": "0.0.0.0",
  "port": 5000,
  "credentialsPath": "C:/Users/Usuario/AppData/Roaming/GrandParfum/serviceAccountKey.json",
  "apiToken": "troque-este-token",
  "allowedOrigins": ["http://localhost:5500", "http://192.168.0.10:5173"]
}
```

O launcher mostra a URL local, a URL de rede quando detectada, o modo Firebase/mock e o resultado do `/health`.

## Configuração Firebase segura

> Atenção: se uma chave Firebase real já foi comitada anteriormente, ela deve ser revogada/rotacionada no Google Cloud/Firebase Console. Remover o arquivo do repositório não invalida uma chave já exposta no histórico Git.

Para usar Firebase, mantenha a chave fora do Git e configure uma variável de ambiente:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/seguro/serviceAccountKey.json"
# ou
export FIREBASE_CREDENTIALS_PATH="/caminho/seguro/serviceAccountKey.json"
```

No Windows, o caminho recomendado para o launcher é:

```text
%APPDATA%\GrandParfum\serviceAccountKey.json
```

Há um exemplo sem segredo real em:

```text
Sistema de vendas/serviceAccountKey.example.json
```

Nunca versione `serviceAccountKey.json`, `.env`, `server_config.json` real, tokens ou chaves privadas.

## Segurança da API

- Se `API_TOKEN` estiver vazio, as rotas de escrita ficam abertas para manter compatibilidade em desenvolvimento.
- Se `API_TOKEN` estiver definido, loja e dashboard devem enviar `Authorization: Bearer <token>`.
- Use `ALLOWED_ORIGINS` para restringir CORS em rede local ou produção.
- Não exponha a porta `5000` diretamente na internet; use VPN, túnel seguro, HTTPS/proxy reverso e token forte.

## Verificações úteis

Valide Python:

```bash
python -m py_compile "Sistema de vendas/config.py" "Sistema de vendas/database.py" "Sistema de vendas/server_headless.py" "Sistema de vendas/api/server.py" "Sistema de vendas/api/routes.py" "Sistema de vendas/api/schemas.py" "Sistema de vendas/launcher.py"
```

Valide a loja:

```bash
node --check "E-commerce/app.js"
node --check "E-commerce/products_live.js"
```

Valide o dashboard:

```bash
cd "Sistema de análise de vendas/React app"
npm install
npm run build
```

## Empacotamento opcional

Para gerar um executável do servidor headless sem embutir credenciais:

```bash
pip install pyinstaller
pyinstaller "Sistema de vendas/pyinstaller_server.spec"
```

O executável continua usando configuração externa por variável de ambiente, arquivo arrastado ou credencial fora do repositório.

## Documentação completa

O guia detalhado de operação local, rede, launcher, credenciais Firebase, segurança e PyInstaller está em:

```text
docs/operacional.md
```

## Observações de beta

- O checkout registra pedidos para o fluxo operacional, mas não processa pagamento real.
- O dashboard depende da API Python para exibir dados reais.
- Se a API não responder, a loja mantém fallback para Firebase em pedidos sem cupom; cupons exigem API disponível.
