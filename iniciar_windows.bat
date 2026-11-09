@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Criando ambiente virtual...
  py -m venv .venv
  if errorlevel 1 (echo Instale Python 3.11 ou superior & pause & exit /b 1)
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if not defined GCF_USER set GCF_USER=colaborador
if not defined GCF_PASSWORD (
  echo Defina GCF_PASSWORD com uma senha forte no terminal antes de iniciar.
  echo Exemplo no CMD: set GCF_PASSWORD=SuaSenhaForte
  pause
  exit /b 1
)
if not defined GCF_DESTINATARIOS set GCF_DESTINATARIOS=%~dp0destinatarios.csv
set GCF_ENVIO_HABILITADO=nao
echo Abra http://127.0.0.1:8000 no navegador
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
