import fitz
from app.validator import CAT, validate,valid_cnpj

def pdf(text):
 doc=fitz.open();p=doc.new_page();p.insert_text((30,50),text,fontname='helv',fontsize=8)
 content=doc.tobytes();doc.close();return content

def test_cnpj():
 assert valid_cnpj('07.657.456/0001-78')
 assert not valid_cnpj('00.000.000/0000-00')

def test_unknown_rejected():
 r=validate(pdf('Documento desconhecido'*15),'simples','declaracao')
 assert not r.approved and r.detected is None

def test_category_type_conflict():
 r=validate(pdf('Exemplo'*20),'normal','declaracao')
 assert not r.approved

def test_corrupted_rejected():
 r=validate(b'%PDF-invalido','simples','das')
 assert not r.approved
