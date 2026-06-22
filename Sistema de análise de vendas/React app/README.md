# Dashboard React de análise de vendas

Este app lê métricas da API Python do sistema logístico.

## Modos suportados

### 1. Modo interno local

Use quando o dashboard roda junto com o sistema logístico:

```bash
VITE_DASHBOARD_MODE=internal_api
VITE_STATS_API_URL=http://127.0.0.1:5000/stats
VITE_API_TOKEN=troque-este-token
```

Com o servidor Python iniciado em modo Firebase, `/stats`, `/orders` e `/products` passam a refletir Firestore automaticamente.

### 2. Modo teste

Use apenas para ensaio visual explícito:

```bash
VITE_DASHBOARD_MODE=test
VITE_ALLOW_OFFLINE_FALLBACK=true
```

Nesse modo o fallback offline pode aparecer sem mascarar produção.

## Regras práticas

- `VITE_STATS_API_URL` é obrigatório no modo `internal_api`.
- O dashboard deriva `/orders` e `/products` automaticamente a partir de `/stats`.
- Se a API não responder e o fallback offline não estiver explicitamente permitido, a UI mostra erro de configuração/conectividade em vez de parecer saudável.
- O fluxo recomendado de produção continua sendo: iniciar o servidor logístico Python com Firebase configurado e apontar o dashboard para ele.
