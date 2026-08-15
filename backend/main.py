from fastapi import FastAPI
from backend.auth.controller import router as auth_router
from backend.database import init_db

app = FastAPI(title="Auth API")

app.include_router(auth_router)


@app.on_event("startup")
async def on_startup():
    await init_db()