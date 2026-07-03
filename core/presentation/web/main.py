from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from core.infrastructure.database.models import Base
from core.infrastructure.database.session import engine
from core.presentation.web.routers import paginas, quiz

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

@app.head("/", include_in_schema=False)
def root_head():
    """Respond to HEAD requests for uptime monitors."""
    return {"status": "ok"}

@app.get("/health", include_in_schema=False)
@app.head("/health", include_in_schema=False)
def health_check():
    """Dedicated health check endpoint for uptime monitors."""
    return {"status": "ok"}

app.include_router(paginas.router)
app.include_router(quiz.router)
