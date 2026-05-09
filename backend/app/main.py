from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, orders, products, stock, summary, warehouses
from app.config import settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.database import SessionLocal
    from app.services.user_service import ensure_default_users

    with SessionLocal() as db:
        ensure_default_users(db)
        if settings.seed_demo_data:
            from app.seed_demo import seed_demo_if_empty

            seed_demo_if_empty(db)
    yield


app = FastAPI(title="Склад и заказы", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(summary.router, prefix=settings.api_prefix)
app.include_router(products.router, prefix=settings.api_prefix)
app.include_router(warehouses.router, prefix=settings.api_prefix)
app.include_router(stock.router, prefix=settings.api_prefix)
app.include_router(orders.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
