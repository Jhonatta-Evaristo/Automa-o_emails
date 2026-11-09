"""Testes isolados para validar a segurança básica do lote, usando PDFs sintéticos."""
import io
import fitz
from app.batch import check_company


def make_pdf(text):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((40, 50), text, fontsize=9)
    data = doc.tobytes()
    doc.close()
    return data


def test_reject_unknown_pdf():
    content = make_pdf('Documento sem identificacao fiscal ' * 10)
    result = check_company([('desconhecido.pdf', content)], 'teste@example.com', lambda *_: True)
    assert not result['approved']
    assert not result['send_enabled']


def test_reject_duplicate():
    pdf = make_pdf('Documento sem identificacao fiscal ' * 10)
    result = check_company([('a.pdf', pdf), ('b.pdf', pdf)], 'teste@example.com', lambda *_: True)
    assert not result['approved']
    assert any('duplicado' in x.lower() for x in result['documents'][1]['reasons'])


def test_reject_not_pdf():
    result = check_company([('arquivo.pdf', b'not-a-pdf')], 'teste@example.com', lambda *_: True)
    assert not result['approved']
