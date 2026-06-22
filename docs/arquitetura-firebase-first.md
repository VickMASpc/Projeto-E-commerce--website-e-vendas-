# Arquitetura Firebase-first

Objetivo: a loja hospedada no GitHub Pages deve operar com Firebase como caminho normal de produção. JSON/mock e API local ficam restritos a testes explícitos.

## Estado alvo

- Loja web (`docs/` e `E-commerce/`): catálogo, autenticação, perfil, carrinho, favoritos e reviews seguem no Firebase.
- Checkout e cupom: passam por Cloud Functions (`createOrder` e `validateCoupon`).
- Backend Python (`Sistema de vendas/`): pode operar em Firebase ou mock, mas mock só entra por configuração explícita.
- React app de análise: consome a API Python (`/stats`, `/orders`, `/products`). Em produção, basta iniciar o servidor logístico com Firebase configurado.

## Contrato canônico de pedido

Todo pedido novo deve ser normalizado para este contrato:

- `id`
- `customer_id`
- `customer_name`
- `customer_email`
- `customer_phone`
- `customer_address`
- `items[]`
- `subtotal`
- `shipping`
- `discount_total`
- `coupon_code`
- `total`
- `status`
- `created_at`
- `updated_at`
- `schema_version`

Observações:

- aliases legados continuam aceitos na leitura (`clienteId`, `clienteNome`, `itens`, `dataCriacao`, `schemaVersion`);
- Cloud Functions gravam o contrato canônico;
- `domain/order.py` normaliza qualquer payload antigo para esse formato.

## Modos do backend Python

Variáveis relevantes:

- `GRAND_PARFUM_MODE=production|development|test`
- `USE_FIREBASE=true|false`
- `GRAND_PARFUM_ALLOW_MOCK=true|false`

Regras:

- `production`: Firebase obrigatório. `USE_FIREBASE=false` é ignorado.
- `development` e `test`: mock só pode ser usado quando:
  - `USE_FIREBASE=false`, ou
  - `GRAND_PARFUM_ALLOW_MOCK=true`

Exemplos:

```powershell
$env:GRAND_PARFUM_MODE="production"
$env:USE_FIREBASE="true"
$env:FIREBASE_CREDENTIALS_PATH="C:\seguro\serviceAccountKey.json"
```

```powershell
$env:GRAND_PARFUM_MODE="test"
$env:USE_FIREBASE="false"
```

## Cloud Functions

Pasta: `functions/`

Funções:

- `health`
- `createOrder`
- `validateCoupon`

Responsabilidades do backend:

- validar payload;
- normalizar aliases legados;
- recalcular subtotal, desconto, frete e total;
- validar estoque e cupom;
- gravar pedido em `pedidos`;
- baixar estoque no servidor.
- gravar pedidos exatamente no contrato canônico com `schema_version`.

## Dashboard e métricas

- `/stats`, `/orders` e `/products` continuam vindo da API Python.
- Quando o servidor logístico sobe com Firebase válido, esses endpoints refletem Firestore.
- O modo offline do dashboard React continua existindo, mas não deve ser usado para mascarar configuração incorreta de produção.

## Normalização de dados antigos

Se houver carga antiga fora do contrato canônico, use:

```powershell
python scripts/normalize_orders.py caminho\para\pedidos.json
```

Por padrão o script gera um novo arquivo `*.normalized.json` sem sobrescrever a origem.

## Regras de segurança

- `produtos`: leitura pública apenas; escrita pública negada.
- `pedidos`: criação direta pelo cliente negada; leitura apenas do dono autenticado.
- `cupons`: sem leitura pública ampla.
- `users`, `carts`, `wishlists`: acesso apenas do dono autenticado.
- `reviews`: criação autenticada; edição só pelo autor.
- `newsletter`: criação controlada; leitura bloqueada.

## App Check para GitHub Pages

1. No console Firebase, abra App Check e registre o app web usado pela loja.
2. Cadastre o domínio do GitHub Pages usado pela loja, por exemplo `vickmaspc.github.io`.
3. Habilite reCAPTCHA Enterprise ou reCAPTCHA v3 para o app web.
4. Faça rollout primeiro em modo monitoramento.
5. Só depois ative enforcement em:
   - Cloud Functions
   - Firestore

Observações:

- A Firebase API key do frontend não é segredo.
- A segurança vem de Firestore Rules, Cloud Functions e App Check.
- Não adicionar `serviceAccountKey.json` real ao repositório.
