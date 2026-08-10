from fastapi import FastAPI

from app.routers import business_rules, chat, health

app = FastAPI(title="ПридПром")

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(business_rules.router)
