"""FastAPI application entrypoint."""
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.api import transactions, me, prizes, admin

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.include_router(transactions.router)
app.include_router(me.router)
app.include_router(prizes.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.app_name}
