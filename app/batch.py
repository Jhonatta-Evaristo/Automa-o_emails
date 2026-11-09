"""Validação isolada por empresa para envios em lote (não envia e-mails)."""
from __future__ import annotations
import hashlib
from .validator import CAT, LABEL, validate, norm

MAX_FILES_PER_COMPANY = 12
MAX_FILE_BYTES = 3_500_000  # orçamento conservador para requisições na Vercel
MAX_REQUEST_BYTES = 4_000_000


def check_company(files: list[tuple[str, bytes]], email: str, allowed) -> dict:
    """Classifica cada arquivo independentemente, valida identidade compartilhada e autorização.

    allowed(email, cnpj) -> bool; nenhuma aprovação autoriza envio nesta versão.
    """
    records = []
    seen_hashes, seen_types = set(), set()
    for filename, content in files:
        # Descobre categoria e tipo real, sem confiar no nome ou seleção do colaborador.
        # 'validate' exige tipo esperado; probe independente para identificar o documento.
        from .validator import classify, extract_cnpj, extract_competence
        import fitz
        item = {'filename': filename, 'approved': False, 'type': None,
                'category': None, 'cnpj': None, 'competence': None, 'reasons': []}
        if not filename.lower().endswith('.pdf') or not content.startswith(b'%PDF-'):
            item['reasons'].append('Arquivo não é um PDF válido.')
        elif len(content) > MAX_FILE_BYTES:
            item['reasons'].append('PDF excede o limite para testes em lote (3,5 MB).')
        else:
            try:
                with fitz.open(stream=content, filetype='pdf') as doc:
                    if doc.is_encrypted or not (1 <= len(doc) <= 30):
                        raise ValueError('PDF protegido ou quantidade de páginas inválida')
                    raw = '\n'.join(p.get_text('text') for p in doc)
                if len(raw.strip()) < 100:
                    item['reasons'].append('PDF sem texto extraível suficiente.')
                else:
                    hits = classify(norm(raw))
                    if len(hits) != 1:
                        item['reasons'].append('Tipo não identificado de forma exclusiva (ou PDF misturado).')
                    else:
                        kind = hits[0]
                        result = validate(content, CAT[kind][0], kind)
                        item.update(type=kind, type_label=CAT[kind][1],
                                    category=CAT[kind][0], category_label=LABEL[CAT[kind][0]],
                                    cnpj=result.cnpj, competence=result.competence)
                        item['reasons'].extend(result.reasons)
            except Exception:
                item['reasons'].append('PDF inválido ou não foi possível ler o conteúdo.')
        digest = hashlib.sha256(content).hexdigest()
        if digest in seen_hashes:
            item['reasons'].append('Arquivo duplicado dentro desta empresa.')
        seen_hashes.add(digest)
        if item['type'] and item['type'] in seen_types:
            item['reasons'].append('Mais de um PDF do mesmo tipo na pasta. Necessária revisão.')
        if item['type']:
            seen_types.add(item['type'])
        records.append(item)

    cnps = {d['cnpj'] for d in records if d['cnpj']}
    periods = {d['competence'] for d in records if d['competence']}
    categories = {d['category'] for d in records if d['category']}
    general = []
    if len(cnps) != 1 or any(not d['cnpj'] for d in records):
        general.append('CNPJ ausente ou documentos de empresas diferentes.')
    if len(periods) != 1 or any(not d['competence'] for d in records):
        general.append('Competência ausente ou documentos de meses diferentes.')
    if len(categories) != 1 or any(not d['category'] for d in records):
        general.append('Categorias incompatíveis ou não identificadas na mesma pasta.')
    cnpj = next(iter(cnps)) if len(cnps) == 1 else None
    if not cnpj or not allowed(email, cnpj):
        general.append('E-mail não autorizado para o CNPJ identificado.')
    approved = bool(records) and not general and all(not d['reasons'] for d in records)
    for item in records:
        item['approved'] = approved and not item['reasons']
    return {'approved': approved, 'cnpj': cnpj, 'competence': next(iter(periods)) if len(periods) == 1 else None,
            'category': next(iter(categories)) if len(categories) == 1 else None,
            'email': email, 'documents': records, 'reasons': general,
            'send_enabled': False,
            'message': 'Lote validado (simulação). O envio real permanece desativado.' if approved else 'Lote bloqueado: corrija os problemas antes de qualquer envio.'}
