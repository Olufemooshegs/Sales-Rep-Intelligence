from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token
from typing import Optional

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, *, email: str, password: str, role: str = "rep") -> User:
    user = User(email=email, hashed_password=hash_password(password), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, *, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_token_for_user(user: User, expires_minutes: Optional[int] = None) -> str:
    data = {"sub": user.email, "role": user.role, "user_id": user.id}
    return create_access_token(data=data, expires_minutes=expires_minutes)
