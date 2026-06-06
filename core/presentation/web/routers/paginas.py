import json
import os
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_capitulos():
    with open(os.path.join("data", "capitulos.json"), "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    capitulos = get_capitulos()
    return templates.TemplateResponse("index.html", {"request": request, "capitulos": capitulos})

@router.get("/capitulo/{id}", response_class=HTMLResponse)
async def capitulo(request: Request, id: int):
    capitulos = get_capitulos()
    capitulo = next((c for c in capitulos if c["id"] == id), None)
    if not capitulo:
        raise HTTPException(status_code=404, detail="Capítulo não encontrado")
    return templates.TemplateResponse("capitulo.html", {"request": request, "capitulo": capitulo})
