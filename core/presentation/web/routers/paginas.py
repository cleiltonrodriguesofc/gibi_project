from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/capitulo/{id}", response_class=HTMLResponse)
async def capitulo(request: Request, id: int):
    # This would fetch from data/capitulos.json
    return templates.TemplateResponse("capitulo.html", {"request": request, "capitulo_id": id})
