# GCF — Automação de documentos v0.4 (validação em lote)

Aplicação FastAPI com interface GCF. Permite **validação individual** de documentos fiscais e **validação em lote por empresa**, com e-mail por empresa e anexos PDF. A versão de hospedagem na Vercel **não envia e-mails**.

Abra **`GUIA_LOTE_ANTIGRAVITY.md`** para as instruções de atualização no Antigravity, GitHub e Vercel.

## Arquivos relevantes

- `app/main.py`: API individual já existente; integra a rota de lote.
- `app/validator.py`: classificações conservadoras de sete tipos de documentos.
- `app/batch.py`: reconhecimento e regras cruzadas dentro da pasta de uma empresa.
- `app/batch_routes.py`: API de validação de até 12 PDFs por empresa.
- `app/index.html`: interface com abas Individual e Em lote.
- `tests/test_batch.py`: testes automatizados, sem documentos de clientes.
- `index.py`: entrada na Vercel.

**Importante:** testes positivos de identificação não garantem ausência de falsos positivos. A versão de lote não está pronta para envio fiscal real. PDFs reais não estão incluídos no projeto.
