from fastapi import FastAPI

from app.routers import chat, health

app = FastAPI(title="ПридПром")

app.include_router(health.router)
app.include_router(chat.router)
