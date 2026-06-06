"""
Main entry point for the Guardiões da Saúde web application.
Initializes FastAPI, mounts static files, includes routers and sets up the database.
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import Base, engine
from routers import paginas, quiz, progresso

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Guardiões da Saúde",
    description="Revista digital interativa de educação em saúde infantil",
    version="1.0.0",
    lifespan=lifespan,
)

# Serve static files (CSS, JS, images, animations)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routers
app.include_router(paginas.router)
app.include_router(quiz.router, prefix="/api")
app.include_router(progresso.router, prefix="/api")
