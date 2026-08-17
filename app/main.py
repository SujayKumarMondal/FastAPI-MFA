import logging
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Ensure project root is on sys.path when running module as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core import settings
from app.db import init_db
from app.routes import auth as auth_router
from app.routes import mfa as mfa_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")

app = FastAPI(title="FastAPI-MFA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error for %s: %s", request.url.path, exc)
    return JSONResponse(status_code=422, content={"detail": exc.errors(include_context=False)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth_router.router)
app.include_router(mfa_router.router)


template_path = Path(__file__).resolve().parent.parent / "templates" / "index.html"


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(template_path.read_text(encoding="utf-8"))


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=6004, reload=True)