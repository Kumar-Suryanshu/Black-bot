from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import router
from backend.app.db import init_db

app = FastAPI(title="Rerun API")

# Allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    import os
    sandbox_type = os.getenv("SANDBOX_TYPE", "docker")
    if sandbox_type == "fake" and os.getenv("ALLOW_FAKE_SANDBOX") != "1":
        raise RuntimeError("Refusing to start API with SANDBOX_TYPE=fake without ALLOW_FAKE_SANDBOX=1.")
    init_db()

