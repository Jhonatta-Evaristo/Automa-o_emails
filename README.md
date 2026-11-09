# GCF — Validação de PDFs e envio por e-mail (protótipo local v0.2)

Este projeto é uma **primeira versão para testes no Antigravity / Windows**, não um sistema homologado. Tela enxuta: **e-mail da empresa → categoria → tipo → PDF → Validar documento → Enviar e-mail**. Não exige digitar nome da empresa. O CNPJ e a competência são **extraídos do PDF**. As regras atuais não podem garantir que o PDF se refere à competência *desejada* sem outro dado de referência.

## Estrutura

```text
gcf_automacao/
├─ app/
│  ├─ __init__.py
│  ├─ main.py              # API, cadastro e envio SMTP
│  ├─ validator.py         # leitura do PDF, 7 classificações e validação
│  ├─ index.html           # interface azul GCF
│  └─ logo.png             # referência de logo fornecida
├─ tests/
│  └─ test_validator.py    # testes automatizados sem dados de clientes
├─ testar_pdfs_reais.py    # teste cruzado opcional com os 7 exemplos
├─ destinatarios_exemplo.csv
├─ .env.exemplo
├─ requirements.txt
└─ iniciar_windows.bat
```

## Como rodar no Windows (recomendado)

1. Instale **Python 3.11 ou superior**. Abra a pasta no Antigravity e abra um terminal **PowerShell** nessa pasta.
2. Execute:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:GCF_USER="colaborador"
$env:GCF_PASSWORD="ESCOLHA_UMA_SENHA_FORTE"
$env:GCF_DESTINATARIOS="$PWD\destinatarios.csv"
$env:GCF_ENVIO_HABILITADO="nao"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. Abra **http://127.0.0.1:8000** e informe usuário `colaborador` e a senha definida. O servidor aceita conexões apenas do seu computador (`127.0.0.1`).
4. Para ativar validações aprovadas, crie **destinatarios.csv** a partir de `destinatarios_exemplo.csv`, usando **o CNPJ real e o e-mail corporativo autorizado**. Esse CSV não é preenchido automaticamente. Sem cadastro válido, nenhum arquivo é aprovado para envio.
5. O botão **Enviar e-mail** somente é habilitado após a validação. **O envio real permanece desligado por padrão**, inclusive no `iniciar_windows.bat`. Não é necessário configurar SMTP para testar a interface e os bloqueios.

> Dica: se a política do Windows impedir ativação de scripts, os comandos acima usam diretamente o Python do ambiente, sem `Activate.ps1`.

## Como testar

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Para testar contra os 7 PDFs originais recebidos (copie-os **por sua conta** para uma pasta local privada, sem subir a repositórios):

```powershell
.\.venv\Scripts\python.exe testar_pdfs_reais.py "C:\Documentos\PDFs-para-teste"
```

Esse script executa **49 verificações** (cada PDF contra os 7 tipos), sem enviar e-mails. Os PDFs reais **não foram incluídos no ZIP**, para proteger dados dos clientes.

## Segurança e limitações

- O servidor identifica categoria/tipo por conjuntos de expressões, exige CNPJ com dígitos verificadores e extrai competência. Também confere se o e-mail digitado está ativo e autorizado **para aquele CNPJ** no CSV. Não permite envio para qualquer endereço apenas por ter formato válido.
- Reprova PDFs ilegíveis ou sem texto selecionável, PDFs com tipos conflitantes, sem CNPJ único e PDFs inválidos. Ainda não tem OCR, antivírus, autenticação via contas corporativas, banco de dados, checagem de histórico de retificações, assinatura fiscal ou prova de autenticidade em órgão oficial.
- Como **não existe campo de competência na tela**, o sistema apenas exibe a competência encontrada no PDF. Para garantir que seja a competência solicitada, essa informação deverá vir de um contexto confiável (ou voltar como campo obrigatório).
- A validação cria autorização temporária de **15 minutos**. Alterar e-mail, categoria, tipo ou anexo desabilita o botão; aprovações não são reutilizáveis. A aprovação não significa que um documento é autêntico ou que a versão é a última.
- Não exponha este protótipo à internet nem a outros computadores na rede; não use documentos de clientes em testes compartilhados. Para uso real, implemente HTTPS, login corporativo, proteção contra CSRF, trilha de auditoria, retenção segura, controle de versões, antivírus e homologação com mais modelos fiscais.
- O retorno de SMTP confirma aceitação pelo servidor para encaminhamento, **não entrega efetiva** ao destinatário.

## Envio real (somente depois de homologação)

O código tem suporte a SMTP com STARTTLS (porta 587) ou SMTP_SSL (porta 465), mas é propositalmente inativo para a fase de testes. Após configurar uma caixa dedicada e controles de segurança, use as variáveis `GCF_SMTP_HOST`, `GCF_SMTP_PORT`, `GCF_SMTP_FROM`, `GCF_SMTP_USER`, `GCF_SMTP_PASSWORD` e `GCF_ENVIO_HABILITADO=sim` **fora do script de teste**. Nunca coloque senhas no código, no ZIP ou no Git.
