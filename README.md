# Card Checker & Mercado Pago Transparent Checkout

Este repositório combina o sistema de verificação de cartões com uma checkout transparente do Mercado Pago pronta para Deploy no Render (SSL automático).

## Estrutura principal
- `app.py`: backend Flask com endpoint `/api/payments` que chama `https://api.mercadopago.com/v1/payments` usando o `MP_ACCESS_TOKEN`.
- `templates/checkout.html`: interface que consome o SDK oficial (`https://sdk.mercadopago.com/js/v2`), monta os campos do cartão e envia o token para o backend.
- `static/css/main.css`: estilo moderno e responsive para o checkout.
- CLI existente (`run_checker.py`, `checkers/`) permanece disponível para geração/execução de templates de checkout.

## Executando localmente

1. Crie e ative um ambiente Python (recomendado).
2. Instale as dependências:

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

   A aplicação será exposta em `http://localhost:5000` (ou `https` se usar um proxy como o Render) e o front-end estará disponível na raiz.

5. O CLI antigo (`run_checker.py`) segue disponível se você quiser usar os checkers e templates já implementados.

## Deploy no Render com SSL

1. Utilize o `render.yaml` e o `Procfile` fornecidos:
   * `render.yaml` registra o serviço como web em Python e define `gunicorn` como start command.
   * `Procfile` reforça a mesma configuração quando o serviço for criado manualmente no dashboard.
2. Configure as variáveis de ambiente necessárias no painel do Render:
   * `MP_PUBLIC_KEY` → chave pública (client-side).
   * `MP_ACCESS_TOKEN` → token de produção (server-side).
3. O Render cuida automaticamente do HTTPS (SSL gratuito) e do redirecionamento para a porta exposta em `$PORT`.
4. Após o deploy, acesse `https://<sua-app>.onrender.com` e verifique o formulário de checkout.

## Front-end e segurança

- O checkout usa apenas o SDK oficial `mercadopago.js`. Nenhuma informação sensível é persistida no servidor.
- O backend só recebe o `token` gerado, além dos dados de `transaction_amount`, `installments` e `payer_email`, e repassa para a API oficial. Caso seja necessário adicionar campos extras (documento, nome, endereço), basta ajustá-los no template e no payload do `create_payment`.

## Próximos passos recomendados

1. Configure os webhooks ou logs que monitorem os pagamentos aprovados (track `status` e `id` retornados pelo Mercado Pago).
2. Configure alertas no Render para notar quando a aplicação falhar ou se os token expirarem.
3. Use cartões de sandbox da documentação do Mercado Pago para validar o fluxo antes de trocar as chaves de teste pelas de produção.
