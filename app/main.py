from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# routers
from app.api import auth, sales, metrics

app = FastAPI(title="Sales Rep Performance Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(metrics.router)


@app.on_event("startup")
async def on_startup():
    # Ensure DB tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Optionally seed initial admin
    if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.services.auth_service import get_user_by_email, create_user
        async with AsyncSession(engine) as session:
            user = await get_user_by_email(session, settings.ADMIN_EMAIL)
            if not user:
                await create_user(session, email=settings.ADMIN_EMAIL, password=settings.ADMIN_PASSWORD, role="admin")


@app.get("/")
async def root():
    return {"status": "ok"}
