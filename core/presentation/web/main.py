from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from core.infrastructure.database.models import Base
from core.infrastructure.database.session import engine
from core.presentation.web.routers import paginas

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Guardiões da Saúde",
    description="Revista digital interativa",
    lifespan=lifespan
)

# Using relative paths for static and templates Assuming the root is `projeto_gibi`
# Need to make sure `static` and `templates` exist at root
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(paginas.router)
