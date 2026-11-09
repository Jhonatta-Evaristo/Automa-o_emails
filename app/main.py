"""API de validação e envio GCF. Bloqueia envio sem cadastro e SMTP configurados."""
from __future__ import annotations
import csv, io, os, re, secrets, smtplib, time, hashlib, logging, json
from email.message import EmailMessage
from pathlib import Path
from threading import Lock
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from .validator import CAT, LABEL, validate

ROOT=Path(__file__).resolve().parent.parent
app=FastAPI(title='GCF | Validação de Documentos', docs_url=None, redoc_url=None)
security=HTTPBasic()
APP_USER=os.getenv('GCF_USER','')
APP_PASSWORD=os.getenv('GCF_PASSWORD','')
_pending={}; lock=Lock(); TTL=900

def auth(credentials:HTTPBasicCredentials=Depends(security)):
 if not APP_USER or not APP_PASSWORD or not(secrets.compare_digest(credentials.username,APP_USER) and secrets.compare_digest(credentials.password,APP_PASSWORD)):
  raise HTTPException(401,'Credenciais inválidas ou não configuradas',headers={'WWW-Authenticate':'Basic'})

def authorized(email,cnpj):
 # Para hospedagem de testes: configuração privada por variável de ambiente.
 # JSON: {"12345678000195": ["fiscal@empresa.com.br"]}
 config=os.getenv('GCF_DESTINATARIOS_JSON','')
 if config:
  try:
   cadastro=json.loads(config)
   enderecos=cadastro.get(cnpj,[])
   if isinstance(enderecos,str): enderecos=[enderecos]
   return email.casefold() in [str(e).strip().casefold() for e in enderecos]
  except (ValueError,TypeError,AttributeError): return False
 path=Path(os.getenv('GCF_DESTINATARIOS',str(ROOT/'destinatarios.csv')))
 if not path.exists(): return False
 try:
  with path.open(encoding='utf-8-sig',newline='') as f:
   for row in csv.DictReader(f):
    if row.get('email','').strip().casefold()==email.casefold() and re.sub(r'\D','',row.get('cnpj',''))==cnpj and row.get('ativo','').strip().lower() in ('1','sim','true'):
     return True
 except Exception: return False
 return False

@app.get('/',response_class=HTMLResponse)
def home(user=Depends(auth)):
 return (ROOT/'app'/'index.html').read_text(encoding='utf-8')

@app.get('/logo.png')
def logo(user=Depends(auth)):
 return FileResponse(ROOT/'app'/'logo.png',media_type='image/png')

@app.get('/api/options')
def options(user=Depends(auth)):
 return {'categories':LABEL,'types':{k:{'category':v[0],'label':v[1]} for k,v in CAT.items()}}

@app.post('/api/validate')
async def validate_api(email:str=Form(...), category:str=Form(...), kind:str=Form(...), document:UploadFile=File(...), user=Depends(auth)):
 email=email.strip().lower()
 if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): raise HTTPException(400,'E-mail inválido')
 if not document.filename or not document.filename.lower().endswith('.pdf'): raise HTTPException(400,'Somente arquivos PDF')
 content=await document.read(12*1024*1024+1)
 if not content.startswith(b'%PDF-'): raise HTTPException(400,'O arquivo não é um PDF válido')
 if len(content)>12*1024*1024: raise HTTPException(413,'PDF acima de 12 MB')
 result=validate(content,category,kind)
 data=result.json()
 if result.approved and not authorized(email,result.cnpj):
  data['approved']=False
  data['reasons'].append('E-mail não autorizado para o CNPJ identificado. Solicite atualização do cadastro de destinatários.')
 data['token']=None
 if data['approved'] and os.getenv('GCF_MODO_VERCEL','nao').lower()!='sim':
  token=secrets.token_urlsafe(32)
  with lock:
   for key,item in list(_pending.items()):
    if item['expires']<time.time(): del _pending[key]
   _pending[token]={'email':email,'cnpj':result.cnpj,'category':category,'kind':kind,'sha256':result.sha256,'pdf':content,'filename':os.path.basename(document.filename),'expires':time.time()+TTL,'user':user.username}
  data['token']=token
 return data

class SendRequest(BaseModel):
 token:str

@app.post('/api/send')
def send_email(payload:SendRequest,user=Depends(auth)):
 if os.getenv('GCF_MODO_VERCEL','nao').lower()=='sim':
  raise HTTPException(503,'Envio de e-mails desativado nesta versão de testes da Vercel.')
 # Consume token atomically; never allow replay of an approval.
 with lock: record=_pending.pop(payload.token,None)
 if not record or record['expires']<time.time(): raise HTTPException(403,'Validação expirada. Valide o PDF novamente.')
 if record['user']!=user.username or not authorized(record['email'],record['cnpj']): raise HTTPException(403,'Destinatário não autorizado.')
 if hashlib.sha256(record['pdf']).hexdigest()!=record['sha256']: raise HTTPException(403,'Arquivo alterado.')
 host=os.getenv('GCF_SMTP_HOST',''); sender=os.getenv('GCF_SMTP_FROM',''); password=os.getenv('GCF_SMTP_PASSWORD',''); smtp_user=os.getenv('GCF_SMTP_USER','')
 if not all((host,sender,smtp_user,password)) or os.getenv('GCF_ENVIO_HABILITADO','').lower()!='sim':
  raise HTTPException(503,'Envio real desabilitado. Configure o SMTP e GCF_ENVIO_HABILITADO=sim.')
 msg=EmailMessage()
 msg['From']=sender; msg['To']=record['email']; msg['Subject']=f'Documento fiscal - {CAT[record["kind"]][1]}'
 msg.set_content('Olá,\n\nSegue em anexo o documento fiscal.\n\nGrupo Conceito Fiscal')
 msg.add_attachment(record['pdf'],maintype='application',subtype='pdf',filename=record['filename'])
 try:
  port=int(os.getenv('GCF_SMTP_PORT','587'))
  if port==465:
   with smtplib.SMTP_SSL(host,port,timeout=20) as smtp:
    smtp.login(smtp_user,password);smtp.send_message(msg)
  else:
   with smtplib.SMTP(host,port,timeout=20) as smtp:
    smtp.ehlo();smtp.starttls();smtp.ehlo();smtp.login(smtp_user,password);smtp.send_message(msg)
 except Exception:
  logging.exception('Falha no SMTP, não repetir automaticamente sem verificar entrega')
  raise HTTPException(502,'Não foi possível confirmar envio. Consulte o serviço de e-mail antes de tentar novamente.')
 logging.info('Envio solicitado por %s; sha256=%s; tipo=%s',user.username,record['sha256'],record['kind'])
 return {'sent':True,'message':'Servidor SMTP confirmou a aceitação do e-mail para envio.'}

# Validação de pastas por empresa: sem envio real e sem tokens de envio.
from .batch_routes import get_router
app.include_router(get_router(auth, authorized))
