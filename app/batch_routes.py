"""Rotas seguras de lote, sem persistência e sem envio real."""
from __future__ import annotations
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from .batch import check_company, MAX_FILES_PER_COMPANY, MAX_REQUEST_BYTES


def get_router(auth, authorized):
    router = APIRouter()

    @router.post('/api/batch/validate-company')
    async def validate_company(
        email: str = Form(...), documents: list[UploadFile] = File(...),
        user=Depends(auth),
    ):
        email = email.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise HTTPException(400, 'Informe um e-mail válido.')
        if not 1 <= len(documents) <= MAX_FILES_PER_COMPANY:
            raise HTTPException(400, f'Selecione de 1 a {MAX_FILES_PER_COMPANY} PDFs por empresa.')
        size = 0
        entries = []
        for file in documents:
            part = await file.read(MAX_REQUEST_BYTES + 1)
            size += len(part)
            if size > MAX_REQUEST_BYTES:
                raise HTTPException(413, 'Envie até 4 MB por empresa nesta versão de testes da Vercel.')
            entries.append((file.filename or 'sem_nome', part))
        return check_company(entries, email, authorized)

    return router
