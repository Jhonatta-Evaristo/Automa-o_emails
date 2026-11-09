"""Regras conservadoras de identificação para os sete modelos estudados.
Não comprova autenticidade fiscal nem substitui validação com fontes oficiais.
"""
from __future__ import annotations
import hashlib
import re
import unicodedata
from dataclasses import dataclass, asdict
import fitz

CAT = {
 'declaracao': ('simples','Declaração Simples Nacional'),
 'extrato': ('simples','Extrato Simples Nacional'),
 'das': ('simples','Guia DAS Simples Nacional'),
 'recibo_simples': ('simples','Recibo Simples Nacional'),
 'dare': ('normal','Guia DARE'),
 'sped_contrib': ('normal','Recibo SPED Contribuições'),
 'sped_fiscal': ('normal','Recibo SPED Fiscal'),
}
LABEL = {'simples':'Documentos Simples Nacional','normal':'Documentos Empresas Lucro Normal'}

@dataclass
class Result:
 approved: bool
 detected: str | None
 category: str | None
 cnpj: str | None
 competence: str | None
 reasons: list[str]
 sha256: str
 def json(self):
  d=asdict(self)
  d['detected_label']=CAT[self.detected][1] if self.detected else None
  d['category_label']=LABEL[self.category] if self.category else None
  return d

def norm(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().upper()
 return re.sub(r'\s+',' ',s)

def valid_cnpj(value):
 value=re.sub(r'\D','',value)
 if len(value)!=14 or len(set(value))==1: return False
 for pos in (12,13):
  weights=list(range(pos-7,1,-1))+list(range(9,1,-1)) if pos==13 else list(range(5,1,-1))+list(range(9,1,-1))
  remainder=sum(int(x)*w for x,w in zip(value[:pos],weights))%11
  digit=0 if remainder<2 else 11-remainder
  if int(value[pos])!=digit: return False
 return True

def extract_cnpj(raw):
 matches=re.findall(r'(?<!\d)\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}(?!\d)',raw)
 valid={re.sub(r'\D','',x) for x in matches if valid_cnpj(x)}
 return next(iter(valid)) if len(valid)==1 else None

def extract_competence(raw, kind):
 t=norm(raw)
 if kind=='das':
  m=re.search(r'PERIODO DE APURACAO\s+([A-Z]+)/(20\d{2})',t)
  months={'JANEIRO':1,'FEVEREIRO':2,'MARCO':3,'ABRIL':4,'MAIO':5,'JUNHO':6,'JULHO':7,'AGOSTO':8,'SETEMBRO':9,'OUTUBRO':10,'NOVEMBRO':11,'DEZEMBRO':12}
  if not m:
   candidates={(months[mo],year) for mo,year in re.findall(r'\b('+'|'.join(months)+r')/(20\d{2})\b',t)}
   if len(candidates)==1:
    mo,year=next(iter(candidates)); return f'{mo:02d}/{year}'
  if m and m[1] in months: return f'{months[m[1]]:02d}/{m[2]}'
 if kind=='recibo_simples':
  m=re.search(r'\b(0[1-9]|1[0-2])/(20\d{2})\s+\d{14,20}\b',t)
  if m: return '/'.join(m.groups())
 if kind=='dare':
  m=re.search(r'(?:REFERENCIA|REFERENCIA/)\s*.*?\b(0[1-9]|1[0-2])/(20\d{2})\b',t)
  # DARE has a reference column; the header and dates may be separated in PDF extraction.
  if not m: m=re.search(r'\b(0[1-9]|1[0-2])/(20\d{2})\b',t)
  return '/'.join(m.groups()) if m else None
 m=re.search(r'PERIODO DE APURACAO(?:\s*\(PA\))?\s*:?\s*(0[1-9]|1[0-2])/(20\d{2})',t)
 if m: return '/'.join(m.groups())
 m=re.search(r'PERIODO(?: DE APURACAO)?\s*:?\s*(?:0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/(20\d{2})\s+A\s+',t)
 if m: return '/'.join(m.groups())
 # SPED PDFs can extract columns out of reading order: use the only full date range.
 if kind in ('sped_contrib','sped_fiscal'):
  candidates=set(re.findall(r'\b\d{2}/(0[1-9]|1[0-2])/(20\d{2})\s+A\s+\d{2}/\d{2}/20\d{2}',t))
  if len(candidates)==1:
   month,year=next(iter(candidates)); return f'{month}/{year}'
 return None

def classify(t):
 specs={
 'declaracao': ['PROGRAMA GERADOR DO DOCUMENTO DE ARRECADACAO DO SIMPLES NACIONAL - DECLARATORIO','RESUMO DA DECLARACAO','INFORMACOES DA RECEPCAO DA DECLARACAO','NUMERO DA DECLARACAO'],
 'extrato':['EXTRATO DO SIMPLES NACIONAL','INFORMACOES DA APURACAO','TOTAL GERAL DA EMPRESA','PGDAS-D'],
 'das':['DOCUMENTO DE ARRECADACAO DO SIMPLES NACIONAL','NUMERO DO DOCUMENTO','COMPOSICAO DO DOCUMENTO DE ARRECADACAO','VALOR TOTAL DO DOCUMENTO'],
 'recibo_simples':['RECIBO DE ENTREGA DA APURACAO NO PGDAS-D','RESUMO DA APURACAO','INFORMACOES DA RECEPCAO DA APURACAO NO PGDAS-D','NUMERO DO RECIBO'],
 'dare':['DOCUMENTO DE ARRECADACAO DE RECEITAS ESTADUAIS - DARE','RELACAO DE PAGAMENTOS','NOSSO NUMERO','LINHA DIGITAVEL'],
 'sped_contrib':['RECIBO DE ENTREGA DE ESCRITURACAO FISCAL DIGITAL - CONTRIBUICOES','VERSAO EFD-CONTRIBUICOES','APURACAO DAS CONTRIBUICOES','PIS/PASEP','COFINS','NUMERO DO RECIBO'],
 'sped_fiscal':['RECIBO DE ENTREGA DE ESCRITURACAO FISCAL DIGITAL','VERSAO SPED FISCAL','INSCRICAO ESTADUAL','HASH DO ARQUIVO','NUMERO DO RECIBO'],
 }
 found=[]
 for key,fragments in specs.items():
  if all(x in t for x in fragments): found.append(key)
 # Strong mutual exclusion of two almost-identical EFD receipts.
 if 'sped_fiscal' in found and ('VERSAO EFD-CONTRIBUICOES' in t or ' - CONTRIBUICOES' in t): found.remove('sped_fiscal')
 if 'sped_contrib' in found and 'VERSAO SPED FISCAL' in t: found.remove('sped_contrib')
 # The archive may contain multiple types in distinct pages: reject ambiguity.
 return found

def validate(pdf_bytes:bytes,selected_category:str,selected_type:str):
 digest=hashlib.sha256(pdf_bytes).hexdigest()
 reasons=[]
 if selected_type not in CAT or CAT.get(selected_type,(None,))[0]!=selected_category:
  return Result(False,None,None,None,None,['Categoria e tipo selecionados são incompatíveis.'],digest)
 if len(pdf_bytes)>12*1024*1024: return Result(False,None,None,None,None,['Arquivo acima do limite de 12 MB.'],digest)
 try:
  doc=fitz.open(stream=pdf_bytes,filetype='pdf')
  if doc.is_encrypted or not 1<=len(doc)<=30: raise ValueError('PDF protegido, vazio ou acima de 30 páginas')
  text='\n'.join(p.get_text('text') for p in doc)
  doc.close()
 except Exception:
  return Result(False,None,None,None,None,['Não foi possível ler o PDF com segurança.'],digest)
 if len(text.strip())<100: return Result(False,None,None,None,None,['PDF sem texto extraível suficiente; requer análise/OCR.'],digest)
 t=norm(text)
 found=classify(t)
 detected=found[0] if len(found)==1 else None
 if len(found)!=1: reasons.append('Documento não identificado de forma exclusiva.' if not found else 'O PDF contém características de documentos diferentes.')
 category=CAT[detected][0] if detected else None
 if detected and detected!=selected_type: reasons.append(f'Tipo incorreto: identificado {CAT[detected][1]} ({LABEL[category]}).')
 cnpj=extract_cnpj(text)
 if not cnpj: reasons.append('CNPJ válido e único não identificado no PDF.')
 competence=extract_competence(text,detected) if detected else None
 if not competence: reasons.append('Competência não identificada com segurança.')
 return Result(not reasons,detected,category,cnpj,competence,reasons,digest)
