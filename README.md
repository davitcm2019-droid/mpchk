# Card Checker & Mercado Pago Transparent Checkout

Este repositorio combina o sistema de verificacao de cartoes com um checkout transparente do Mercado Pago pronto para deploy no Render (SSL automatico).

## Estrutura principal
- `app.py`: backend Flask com os endpoints `/`, `/api/config` e `/api/payments`, usando `MP_ACCESS_TOKEN` para criar pagamentos via `https://api.mercadopago.com/v1/payments`.
- `templates/checkout.html`: interface que carrega o SDK oficial (`https://sdk.mercadopago.com/js/v2`), monta o cardForm do Mercado Pago e adiciona a nova area de processamento em lote.
- `static/css/main.css`: estilos leves para o dashboard e para os cards de resultados (Live/Die/CVV inválido).
- As ferramentas antigas (`run_checker.py`, `checkers/`) continuam disponiveis para gerar templates e validar gateways.

## Executando localmente

1. Crie e ative um ambiente Python (recomendado).
2. Instale as dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Copie `.env.example` para `.env` e preencha:

   ```ini
   MP_PUBLIC_KEY=pk_test_...
   MP_ACCESS_TOKEN=ACCESS_TOKEN_AQUI
   PORT=5000
   ```

4. Execute o backend:

   ```bash
   python app.py
   ```

   A aplicacao sera exposta em `http://localhost:5000` (ou `https` se usar um proxy) e o front-end fica disponivel na raiz.

5. O CLI antigo (`run_checker.py`) continua disponivel caso voce queira manter o fluxo atual de checkers.

## Deploy no Render com SSL

1. Use o `render.yaml` e o `Procfile` fornecidos:
   * `render.yaml` declara o servico web Python e define o `startCommand` do Gunicorn.
   * `Procfile` garante o mesmo comando caso voce prefira criar o servico manualmente.
2. Configure as variaveis de ambiente no painel do Render:
   * `MP_PUBLIC_KEY` – chave publica usada no frontend.
   * `MP_ACCESS_TOKEN` – token privado usado no backend.
3. O Render cuida automaticamente do HTTPS e do redirecionamento para a porta injetada em `$PORT`.
4. Acesse `https://<seu-servico>.onrender.com` depois do deploy para checar o dashboard.

## Front-end e seguranca

- O checkout usa apenas o SDK oficial `mercadopago.js`. Dados sensiveis jamais ficam no servidor, apenas o token criado pelo SDK.
- O backend repassa o token, `transaction_amount`, `installments` e `payer_email` diretamente para a API oficial. Se voce precisar de campos extras (nome, documento, endereco), basta adaptar o template e o payload do `create_payment`.
- O campo de valor default do form unico esta fixado em R$ 3,00, o mesmo valor cobrado em cada tentativa automatica da lista.

## Teste em lote de cartoes

- Cole os cartoes no campo de lista usando o padrao `cardNumber|MM|YYYY|CVV`. Linhas vazias ou comentarios iniciados em `#` sao ignoradas.
- O frontend gera nomes e CPFs validos automaticamente e dispara R$ 3,00 por cartao, exibindo os resultados no dashboard.
- As respostas sao agrupadas em listas separadas para `Live`, `Die` e `CVV inválido`, com a mesma interface responsiva e explicacoes do status retornado pelo Mercado Pago.
- Use os cartoes de sandbox da documentacao para validar tudo antes de trocar pelas credenciais de producao.

## Proximos passos recomendados

1. Configure webhooks ou logs que monitorem os pagamentos aprovados (faca tracking de `status` e `id` retornados pelo Mercado Pago).
2. Defina alertas no Render caso o servico falhe ou os tokens expirem.
3. Rode a checklist com os cartoes de sandbox para garantir que o fluxo funciona antes de mudar para credenciais reais.
