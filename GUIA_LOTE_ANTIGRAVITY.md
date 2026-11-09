# GCF — atualização para validação em lote v0.4

Esta atualização **não envia e-mails** em lote. Primeiro valide com arquivos sintéticos ou PDFs expressamente autorizados para homologação.

## O que muda

- Aba **Individual**: permanece como na versão anterior.
- Aba **Em lote**: para cada empresa, digite um e-mail e anexe vários PDFs. Clique `+ Adicionar empresa` para repetir.
- Alternativa: `Selecionar pasta principal` importa subpastas por empresa e cria os cartões; **os e-mails devem ser preenchidos manualmente** em cada cartão.
- Clique **Validar lote**: o navegador envia **uma empresa por vez** à API para identificar todos os documentos, CNPJ, competência e conferência do e-mail autorizado.
- Se faltar informação, houver documento de outro CNPJ, outra competência, categoria diferente, repetição de tipo ou arquivo duplicado, **a empresa inteira é bloqueada**. Outras empresas são avaliadas separadamente.
- O botão de envio em lote fica sempre desabilitado na v0.4. **Nenhum e-mail é disparado**.

## Como atualizar sem perder seus dados

1. Faça uma cópia da pasta `automacao_email` e de qualquer arquivo local de configuração, fora do Git.
2. Extraia este ZIP. Copie os arquivos e pastas do ZIP para a **raiz do seu projeto** `automacao_email`, substituindo arquivos com os mesmos nomes.
3. Não copie PDFs reais, `.env`, CSVs privados, credenciais ou senhas para o GitHub.
4. Confira seu `.gitignore`, depois faça os comandos abaixo na pasta `automacao_email`.

## Testar no Windows / Antigravity

```powershell
cd "C:\Users\GCF 01\Desktop\automacao_email"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:GCF_USER="colaborador"
$env:GCF_PASSWORD="SUA_SENHA_NOVA"
$env:GCF_MODO_VERCEL="sim"
$env:GCF_ENVIO_HABILITADO="nao"
$env:GCF_DESTINATARIOS_JSON='{"12345678000195":["teste@example.com"]}'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

O JSON acima é apenas **exemplo de formato**; use CNPJs e endereços autorizados em homologação e nunca publique os dados no Git. Depois abra http://127.0.0.1:8000.

O limite para testes em lote na Vercel é conservador: **4 MB por empresa / requisição e até 12 PDFs**. O lote pode ter muitas empresas, mas o navegador deve ficar aberto durante a validação. Cada empresa é verificada separadamente.

## Publicar no GitHub e Vercel

```powershell
git status
git add app/main.py app/batch.py app/batch_routes.py app/index.html tests/test_batch.py GUIA_LOTE_ANTIGRAVITY.md README.md
git status
git commit -m "Adicionar validacao de documentos em lote"
git push origin main
```

A Vercel deverá criar um novo deploy. Se necessário, acesse **Deployments** e use **Redeploy**. Mantenha:

```text
GCF_MODO_VERCEL=sim
GCF_ENVIO_HABILITADO=nao
```

Os e-mails autorizados são configurados em `GCF_DESTINATARIOS_JSON` nas variáveis protegidas da Vercel, nunca no repositório. A variável é um JSON com CNPJ sem pontuação como chave e uma lista de endereços autorizados.

## Limitações essenciais

Esta versão ainda **não** confere a competência *esperada* com uma referência externa nem a versão mais recente de uma retificação, não implementa auditoria persistente ou cadastro corporativo, nem compara o número da apuração entre todos os PDFs. Uma combinação de PDFs originais e retificadores pode passar na validação individual. **Não use esta versão para envios reais a clientes.**

Para produção, serão necessários armazenamento privado, persistência da validação e autorização dos envios, fila, serviço de e-mail, log de auditoria, confirmação de destinatários e regras de consistência de versões. A hospedagem pública do protótipo com autenticação básica não deve ser tratada como segurança suficiente para dados confidenciais.
