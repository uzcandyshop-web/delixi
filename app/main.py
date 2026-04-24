"""FastAPI application entrypoint."""
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.api import transactions, me, prizes, admin
from app.db import SessionLocal
from app.services.exchange_rate import ensure_rate_fresh

settings = get_settings()
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("delixi.api")

app = FastAPI(title=settings.app_name, version="1.0.0")

app.include_router(transactions.router)
app.include_router(me.router)
app.include_router(prizes.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def _on_startup() -> None:
    """Fetch today's USD rate from cbu.uz on API startup."""
    try:
        with SessionLocal() as db:
            rate = ensure_rate_fresh(db)
            log.info("USD rate on startup: %s UZS/USD", rate)
    except Exception as e:
        log.warning("startup rate refresh failed: %s", e)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.app_name}
