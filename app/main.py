import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Ensure project root is on sys.path when running module as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import init_db
from app.routes import auth as auth_router
from app.routes import mfa as mfa_router

app = FastAPI(title="FastAPI-MFA Backend")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth_router.router)
app.include_router(mfa_router.router)


template_path = Path(__file__).resolve().parent.parent / "templates" / "index.html"


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(template_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=6004, reload=True)