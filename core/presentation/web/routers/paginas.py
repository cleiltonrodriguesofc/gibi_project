import json
import os
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_capitulos() -> list:
    """Load chapters data from JSON file."""
    with open(os.path.join("data", "capitulos.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def get_unidades() -> list:
    """Load health units data from JSON file."""
    path = os.path.join("data", "unidades.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main cover page with all chapters."""
    capitulos = get_capitulos()
    return templates.TemplateResponse("index.html", {"request": request, "capitulos": capitulos})


@router.get("/capitulo/{id}", response_class=HTMLResponse)
async def capitulo(request: Request, id: int):
    """Render a specific chapter page."""
    capitulos = get_capitulos()
    capitulo = next((c for c in capitulos if c["id"] == id), None)
    if not capitulo:
        raise HTTPException(status_code=404, detail="Capítulo não encontrado")
    return templates.TemplateResponse("capitulo.html", {"request": request, "capitulo": capitulo})


@router.get("/mapa", response_class=HTMLResponse)
async def mapa(request: Request):
    """Render the interactive health units map page."""
    unidades = get_unidades()
    return templates.TemplateResponse("mapa.html", {"request": request, "unidades": unidades})
