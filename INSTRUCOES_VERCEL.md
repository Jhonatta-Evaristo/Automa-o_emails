# GCF — Hospedagem de testes na Vercel

**Esta versão é somente para testes de interface e validação. E-mails reais estão desabilitados.** O endpoint de envio permanece bloqueado no servidor. Não subir PDFs de clientes ou cadastro privado ao GitHub.

## Importante sobre a arquitetura
A versão original usa memória temporária para aprovar e-mails; ela não funciona de maneira confiável entre requisições em funções serverless. Esta versão desativa o envio no ambiente Vercel. Para envio em produção, será necessário um armazenamento transacional ou fluxo de validação/envio atômico, trilhas de auditoria e autenticação corporativa.

## 1. Subir para o GitHub
Crie um repositório **privado** e adicione os arquivos da pasta `gcf_vercel`, incluindo `index.py` e `.python-version`. **Não adicione** .env, PDFs, listas privadas de e-mails, senhas ou dados de clientes.

## 2. Importar na Vercel
Em https://vercel.com/new escolha o repositório. Root Directory deve ser o diretório que contém `index.py`, `requirements.txt` e `app/` (raiz do projeto). Configure o preset FastAPI/Python se detectado; não configure build command.

## 3. Variáveis de ambiente da Vercel
Em Project Settings > Environment Variables configure:

- `GCF_USER`: `colaborador` (ou usuário à sua escolha)
- `GCF_PASSWORD`: uma senha **nova, longa e exclusiva** (não reutilize a senha mencionada em chats).
- `GCF_MODO_VERCEL`: `sim` (obrigatório para impedir envio)
- `GCF_ENVIO_HABILITADO`: `nao`
- `GCF_DESTINATARIOS_JSON`: opcional, JSON com CNPJ apenas com dígitos e e-mails autorizados. Exemplo fictício: `{"12345678000195":["fiscal@empresa-exemplo.com.br"]}`. Use apenas CNPJs válidos e dados autorizados. **Não inclua esse cadastro em Git**.

As variáveis devem ser definidas nos ambientes Preview e/ou Production conforme o deploy. Depois faça Redeploy para carregá-las.

## 4. Testar
Entre na URL gerada pela Vercel. O navegador solicitará as credenciais. Escolha a categoria e o tipo, anexe um PDF de TESTE (sem dados sigilosos) e valide. Sem o cadastro de autorização não haverá aprovação final para um destinatário; o resultado explicará o bloqueio.

O botão Enviar permanecerá desabilitado na Vercel, mesmo após aprovação documental, porque a versão cloud é somente demonstrativa. A Vercel não guarda os tokens temporários de validação de forma compartilhada.

## 5. Segurança adicional
Não compartilhe URL e credenciais publicamente. HTTP Basic é apenas barreira mínima de protótipo e não substitui login corporativo, MFA, limitação de tentativas e auditoria. Não use a versão de testes para envio de documentos reais.

## Rodar localmente com os mesmos arquivos

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:GCF_USER="colaborador"
$env:GCF_PASSWORD="SENHA_FORTE_NOVA"
$env:GCF_MODO_VERCEL="sim"
$env:GCF_ENVIO_HABILITADO="nao"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Aviso:** a validação atual é baseada nos 7 exemplos originais, e não verifica autenticidade oficial ou se a apuração é a retificadora mais recente. A competência é extraída, mas não comparada com uma competência escolhida.
