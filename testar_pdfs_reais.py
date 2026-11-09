"""Teste local dos 7 PDFs reais. Não envia e-mails e não copia PDFs para a pasta do projeto."""
from pathlib import Path
import sys
from app.validator import CAT, validate

FILES = {
    'BABETTE - DECLARAÇÃO SIMPLES NACIONAL - 09.26.pdf': 'declaracao',
    'BABETTE - EXTRATO SIMPLES NACIONAL - 09.26.pdf': 'extrato',
    'BABETTE - GUIA DAS SIMPLES NACIONAL - 09.26.pdf': 'das',
    'BABETTE - RECIBO SIMPLES NACIONAL - 09.26.pdf': 'recibo_simples',
    'JOACIR I - GUIA DARE ICMS 07.2026.pdf': 'dare',
    'RECIBO SPED CONTRIBUICOES.pdf': 'sped_contrib',
    'RECIBO SPED FISCAL.pdf': 'sped_fiscal',
}

def main(folder: Path):
    total=0; failed=0
    for filename,expected in FILES.items():
        path=folder/filename
        if not path.exists():
            print(f'AUSENTE: {filename}')
            failed+=1
            continue
        content=path.read_bytes()
        for kind,(category,_) in CAT.items():
            got=validate(content,category,kind)
            should_approve=(kind==expected)
            if got.approved!=should_approve or got.detected!=expected:
                print(f'FALHA: {filename} / pedido={kind} / aprovado={got.approved} / detectado={got.detected} / motivos={got.reasons}')
                failed+=1
            total+=1
        print(f'TESTADO: {filename} (identificação e recusas cruzadas)')
    print(f'\n{total} verificações, {failed} falhas')
    return 1 if failed else 0

if __name__=='__main__':
    if len(sys.argv)!=2:
        print('Uso: python testar_pdfs_reais.py "C:\\caminho\\para\\os\\7 PDFs"')
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
