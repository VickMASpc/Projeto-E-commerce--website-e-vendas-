# Requisitos
* É necessária a extenção Live server e live preview para acessar o site localmente.

# Como acessar
1. abra o terminal dentro do projeto (crtl+') e rode o comando:
```bash

pip install firebase-admin

```
2. Rode o aplictvo python para iniciar o servidor. (!Pode ser necessário atualizar o arquivo `serviceAccountKey.json`")
3. No VS code, clique com o botão direito em index.html e selecione "Open with Live Server".

# Firebase

## Funcional
* Produtos adicionados pelo sistema são guardados
* Pedidos realizados são contabilizados e podem ser despachados
* Os produtos e pedidos seguem a padronização perf-xxxxx e ord-xxxxx.
* Os produtos são atualizados no site automaticamente.

# E-commerce (Website)

## Funcional
* Lista de produtos
* Carrinho funcional
* Checkout conectado ao sistema python

## Problemas
* Reiews placeholder
* Dados de frete, email, telefone e endereço são placeholder
* Nenhum dos acessos no rodapé são funcionais, são apenas toasts (exceto os da seção "Loja", que são redirects)
* Sistema de favoritos está implementado em partes (é possível selecionar mas não registrar ou checar)
