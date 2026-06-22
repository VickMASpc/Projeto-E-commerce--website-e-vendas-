# Guia de Produção: GitHub Pages e Firebase

Este documento detalha o fluxo real de produção do sistema E-commerce Grand Parfum, a arquitetura, o deploy e as operações diárias.

## 1. Arquitetura Final

A arquitetura de produção do sistema ("Firebase-first") é composta por:

- **Frontend da Loja (GitHub Pages)**: Hospedagem estática do site de E-commerce. A comunicação com o backend é feita diretamente com os serviços do Google Firebase. Não utiliza APIs Python locais em produção para clientes finais externos.
- **Backend (Firebase)**:
  - **Firebase Authentication**: Gerenciamento seguro de acesso de clientes à loja.
  - **Firestore (Banco de Dados)**: Guarda produtos, pedidos, cupons, usuários.
  - **Cloud Functions**: Executam a lógica crítica de regras de negócio (calcular total, frete, cupons, e gerar pedido canônico final na nuvem de forma atômica).
- **Sistema de Logística (Desktop Python)**: O backoffice/Caixa/Estoque. É um App Desktop que roda em um ou mais computadores dentro da operação/escritório local. Ele usa a biblioteca Firebase Admin enviando e sincronizando os pedidos do Firebase.  
- **Dashboard (React)**: Painel de gestão corporativa usado pelos gerentes, consome resultados e métricas do Python API que está rodando em paralelo no computador que hosteia a Logística local.

_Atenção:_ JSON/mock (`db_mock.json`) e IPs em `localhost` são estritamente para simulação e teste em ambiente de desenvolvimento local, sem qualquer impacto no mundo real da loja online do github pages. 

### Por que `localhost` não funciona para clientes externos?
`localhost` é a tradução em rede para "este exato computador que estou usando agora". Se a loja for enviada ao ar mandando buscar de `http://localhost:5000/orders`, quando um cliente abrir o celular em sua residência, o site tentará buscar a porta 5000 no celular desse cliente (inexistente), em vez de ir ao computador da sua empresa. Por isso na nuvem utilizamos as Firebase Cloud Functions, pois elas operam em um domínio da web visível ao mundo com regras controladas, atuando como seu servidor global.

### Por que chaves secretas e "Tokens" no frontend não são segurança real?
Qualquer arquivo ou bloco de código entregue para visualização na Internet – como JS, CSS e HTML – é lido pelo navegador do cliente para a reprodução visual. O código inteiro, até o que não está visível com layout, pode ser visto apertando F12. Um "Token Secreto de Admin" não garante segurança nenhuma injetado ali, podendo ser raptado pelo primeiro visitante.
A conexão Web Firebase, entretanto, utiliza uma chave inofensiva ("Web API Key"), que só indica pro Google qual projeto você quer visualizar, quem fará as garantias e o bloqueio de segurança na verdade serão as Regras do Firestore e os atestados do App Check.

## 2. Deploy em Produção (Nuvem Web)

### Cloud Functions e Firestore Rules
Para publicar a parte lógica backend na conta em nuvem Firebase:
1. Pelo terminal local (com Node/firebase-cli instalados), autentique na plataforma: 
   `firebase login`
2. Envie suas definições de leitura e permissões da base de dados:
   ```bash
   firebase deploy --only firestore:rules
   ```
3. Instale módulos necessários na pasta da nuvem e mande executar o deploy das funções da operação em backend real:
   ```bash
   cd functions
   npm install
   cd ..
   firebase deploy --only functions
   ```

### Deploy / Redeploy do GitHub Pages (Loja Vue/Vanilla JS)
As atualizações de site e produtos ocorrem nativamente:
1. Caso edite arquivos (`/E-commerce/index.html` ou em `/docs`), certifique-se de não estar utilizando artimanhas do modo dev via `localhost`. O código já deve chamar Firebase onCall `createOrder`.
2. Adicione e aplique commits por Git: `git add .` seguido de `git commit -m "Nova melhoria na home"`.
3. Sincronize: `git push origin main`.
4. As `GitHub Pages` atualizarão em poucos minutos o cache no servidor espelho da web e refletirão o site ao vivo.

### Coleções Básicas do Firestore na Nuvem
- `produtos`: Tudo de inventário (Leitura liberada, apenas escrito pelo Servidor).
- `pedidos`: Onde as funções da nuvem confirmam vendas bem sucedidas aos consumidores. O sistema Logística captura aqui.
- `cupons`: Configurações ativas de desconto e expiração. Restrito apenas à validação de sistema e leitura por Function.
- `users`, `carts`: Usuários podem ver seu próprio ID e carrinho no site mas nunca listar de outras contas.

### Habilitar Firebase App Check
Previne scripts piratas, falsidade ideológica nas rotas API, e abusos com Spam/DDoS de requisições que podem inchar as despesas da Google:
1. No Console Web Firebase, clique em App Check.
2. Adicione proteção reCAPTCHA Enterprise para o app "Web". Registre no reCAPTCHA os domínios (ex `vickmaspc.github.io`).
3. Adicione o token fornecido de reCAPTCHA no Firebase e insira o script correspondente no HTML e `firebase-config.js` do frontend.
4. Teste em modo "Apenas Monitoramento". Quando estável e confirmado limpo, habilite o Enforcing (Aplicação Estrita) para Firestore e Functions no próprio painel.

## 3. Gestão e Operação (Desktop Local)

Enquanto a rede gira online e clientes compram pela Loja Web do Firebase, em sua empresa você abre o caixa e acompanha o sistema.

### Configurar Autenticação de Administrador (serviceAccountKey)
A sua operação Python exige uma chave para bypass nas regras de segurança, permitindo atualizar o estoque que clientes não podem manusear livremente:
1. Console Firebase > Opções de Projeto > Contas de Serviço (Service Accounts).
2. "Gerar Nova Chave Privada". Ela será em `.json`.
3. Armazene fora da base do Github (exemplo em ambiente Windows: `C:\Users\SuaConta\AppData\Roaming\GrandParfum\serviceAccountKey.json`).
4. **Alerta Crítico**: Se adicionada a chave real na base do Git, hackers roubarão e apagarão todo o firebase minando os custos da sua cloud. Arquivamentos deletados no repositório continuam lá visíveis pelos logs antigos. Nunca commite! 

### Revogação e Rotação de Chaves Expostas
Se acidentalmente publicou a chave ou alguém a viu na tela em aberto: acessar o Console Google Cloud (IAM Admin > Acessos e Serviço das contidas) ou Console Firebase > Contas de Serviço, selecionar a dita chave exposta, **excluí-la irrevesívelmente (revoke)**, e prosseguir gerando a nova que deve ser colada no diretório seguro da sua máquina local novamente.

### Ligar o Sistema (Terminal) - Todo Dia
A operação deve ser iniciada de modo explícito de ambiente `production`, rodando as funções a seguir pelo prompt com root no servidor Desktop da sua sede:

**Painel Visual Windows Administrativo completo de Vendas:**
```powershell
$env:GRAND_PARFUM_MODE="production"
$env:USE_FIREBASE="true"
$env:FIREBASE_CREDENTIALS_PATH="C:\caminho\seguro\serviceAccountKey.json"
python "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
```

**Para Iniciar estritamente Processos Backend sem as Janela Windows (para painéis Dashboard):**
```powershell
$env:GRAND_PARFUM_MODE="production"
$env:USE_FIREBASE="true"
$env:FIREBASE_CREDENTIALS_PATH="C:\caminho\seguro\serviceAccountKey.json"
python "Sistema de vendas/server_headless.py"
```

#### Comandos de Testes (Mock/Local)
Em ambientes de testes com a variável em dev, os faturamentos online ignorarão os repositórios remotos e o sistema atuará consumindo o JSON falso no HD da maquina, bom para ver interfaces sem sujar contas ativas ou Firebase falso.
```powershell
$env:GRAND_PARFUM_MODE="development"
$env:USE_FIREBASE="false"
python "Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py"
```
_(A documentação lembra que Mocks local nunca responderão online e devem se restringir a exploração técnica sem Firebase.)_

## 4. Checklist: Validação Completa e Vida
Após subirmos tudo isto, garanta a funcionalidade por meio dessa testagem geral:

- [ ] (A) Loja abre via URL global (GitHub Pages, e não um port 127.0.0.1 em live server local).
- [ ] (B) Produto da Vitrine tem os dados idênticos listados pelo Firestore (Preço, nome etc atualizados).
- [ ] (C) Na simulação de Carrinho com conta válida no site e Cupom aplicado na confirmação, ocorre o cálculo com Functions Firebase, e é autorizado pela Cloud Function retornando os custos corretos.
- [ ] (D) O Pagamento processado cria com sucesso e imediato o ticket na coleção Firestore `pedidos` (Verificado via Admin console Web Google).
- [ ] (E) A quantidade virtual desse produto adquirido foi decrementada em Firestore (`estoque baixa` via trigger ou Functions de checkout).
- [ ] (F) No ambiente do seu escritório, o "Sistema de Logística da Retaguarda", ligado em modo Production/Firebase pelo Desktop detectou e consumiu esse pedido.
- [ ] (G) O Dashboard interno visual local (`React app` no escritório local) lê essas atualizações pelo sistema headless e repassa faturamento/visões no dashboard em `/orders` e nas planilhas do mês validando que as verbas foram integradas.
