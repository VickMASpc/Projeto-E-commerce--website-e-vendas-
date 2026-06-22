# Guia operacional — Grand Parfum

Este guia explica como iniciar o sistema desktop, a API headless, a loja e o dashboard em modo local ou em outro computador da rede. Não há segredos reais neste documento.

## 1. Rodar modo desktop

Use o modo desktop quando quiser abrir o backoffice com interface CustomTkinter e a API local integrada:

```bash
python "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
```

A API fica disponível por padrão em `http://localhost:5000`. Se não houver credencial Firebase válida, o sistema usa o modo JSON/mock local.

## 2. Rodar servidor headless local

Use o modo headless quando quiser iniciar somente a API, sem abrir janela:

```bash
python "Sistema de vendas/server_headless.py"
```

O servidor imprime a URL de `/health`, o host, a porta, o modo Firebase/mock e permanece ativo até `Ctrl+C`.

## 3. Rodar servidor em outro computador da rede

No computador que será o servidor, configure host, porta, token, CORS e credencial por variáveis de ambiente ou `server_config.json` externo:

```bash
API_HOST=0.0.0.0
API_PORT=5000
FIREBASE_CREDENTIALS_PATH=C:\Users\Usuario\AppData\Roaming\GrandParfum\serviceAccountKey.json
API_TOKEN=troque-este-token
ALLOWED_ORIGINS=http://localhost:5500,http://192.168.0.10:5173
python "Sistema de vendas/server_headless.py"
```

No Windows PowerShell, use o formato `$env:NOME="valor"` antes de executar o Python.

## 4. Descobrir IP do computador servidor

No Windows:

```bat
ipconfig
```

Procure o `Endereço IPv4` da placa de rede ativa, por exemplo `192.168.0.10`. Em Linux/macOS:

```bash
ip addr
# ou
ifconfig
```

Depois teste em outro computador da mesma rede:

```bash
curl http://192.168.0.10:5000/health
```

## 5. Liberar porta no firewall local

Se outro computador não conseguir acessar a API, libere a porta configurada (`5000` por padrão) no firewall do computador servidor.

No Windows, abra **Segurança do Windows > Firewall e proteção de rede > Configurações avançadas > Regras de Entrada** e crie uma regra TCP para a porta `5000`, restrita ao perfil/rede local quando possível.

## 6. Configurar loja para apontar ao servidor remoto

Antes de carregar a loja, defina a URL e, se usado, o token. Você pode colocar em um script local não versionado ou executar no console do navegador:

```js
window.GRAND_PARFUM_API_URL = "http://192.168.0.10:5000";
window.GRAND_PARFUM_API_TOKEN = "troque-este-token";
```

Também é possível persistir no navegador:

```js
localStorage.setItem("GRAND_PARFUM_API_URL", "http://192.168.0.10:5000");
localStorage.setItem("GRAND_PARFUM_API_TOKEN", "troque-este-token");
```

A loja usa `http://localhost:5000` somente como fallback centralizado para desenvolvimento. Cupons exigem que a API esteja disponível; pedidos sem cupom ainda podem cair no fallback Firebase existente quando a API não responde.

## 7. Configurar dashboard para apontar ao servidor remoto

No dashboard React, crie `.env` a partir de `.env.example`:

```bash
VITE_STATS_API_URL=http://192.168.0.10:5000/stats
VITE_API_TOKEN=troque-este-token
```

O dashboard usa `/stats` como base e deriva `/orders` e `/products` automaticamente. Se a API não responder, o estado offline continua sendo exibido.

## 8. Usar `LIGAR_SERVIDOR.bat` arrastando arquivos

Na pasta `Sistema de vendas/`, arraste um arquivo sobre `LIGAR_SERVIDOR.bat`.

### Arrastar `server_config.json`

Exemplo seguro sem segredo real:

```json
{
  "host": "0.0.0.0",
  "port": 5000,
  "credentialsPath": "C:/Users/Usuario/AppData/Roaming/GrandParfum/serviceAccountKey.json",
  "apiToken": "troque-este-token",
  "allowedOrigins": ["http://localhost:5500", "http://192.168.0.10:5173"]
}
```

O launcher valida campos, define as variáveis equivalentes e inicia o servidor.

### Arrastar `serviceAccountKey.json`

O launcher valida que o arquivo é uma service account Firebase JSON, copia para `%APPDATA%\GrandParfum\serviceAccountKey.json`, define `FIREBASE_CREDENTIALS_PATH` e inicia a API. O conteúdo da chave e a `private_key` nunca são impressos no terminal.

## 9. Credenciais Firebase

- Local recomendado no Windows: `%APPDATA%\GrandParfum\serviceAccountKey.json`.
- Local equivalente em Linux/macOS: um diretório fora do repositório, por exemplo `~/.grandparfum/serviceAccountKey.json`.
- Nunca versionar `serviceAccountKey.json`, `.env`, `server_config.json` real ou qualquer arquivo com token/chave.
- Se uma chave real já foi comitada ou compartilhada, revogue/rotacione no Google Cloud/Firebase Console. Remover do Git não invalida uma chave já exposta.

## 10. Segurança antes de expor fora da rede local

Antes de qualquer acesso remoto fora da LAN:

- Defina `API_TOKEN` forte e configure a loja/dashboard para enviar o mesmo token.
- Restrinja `ALLOWED_ORIGINS` aos domínios/hosts necessários.
- Use HTTPS via proxy reverso, túnel seguro ou VPN.
- Não exponha a porta `5000` diretamente na internet.
- Não imprima, copie ou envie `private_key` em logs, issues ou mensagens.

## 11. Gerar executável com PyInstaller

Instale o PyInstaller no ambiente Python usado pelo sistema:

```bash
pip install pyinstaller
```

A partir da raiz do repositório, gere o executável headless:

```bash
pyinstaller "Sistema de vendas/pyinstaller_server.spec"
```

O spec gera `GrandParfumServer.exe` sem embutir `serviceAccountKey.json`, `.env` real ou `server_config.json` real. O executável continua aceitando configuração externa por arquivo arrastado, variáveis de ambiente ou credencial copiada para `%APPDATA%\GrandParfum\`.

Exemplo de uso do executável gerado:

```bat
GrandParfumServer.exe C:\caminho\para\server_config.json
GrandParfumServer.exe C:\caminho\para\serviceAccountKey.json
```

Se preferir, edite `Sistema de vendas/LIGAR_SERVIDOR.bat` conforme os comentários do próprio arquivo para trocar `python launcher.py` pelo executável gerado.
