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
    init_db()

