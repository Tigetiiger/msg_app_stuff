from typing import cast
from passlib.context import CryptContext
from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis
import uuid

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=131073,
    argon2__time_cost=3,
    argon2__parallelism=2,
)


def hash_with_argon2(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_hash(plain: str, hash: str) -> bool:
    return pwd_context.verify(plain, hash)


def needs_rehash(hash: str) -> bool:
    return pwd_context.needs_update(hash)


class token_auth:
    def __init__(self):
        self.redis_session: redis.Redis = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )

    def generate_token(self) -> str:
        return str(uuid.uuid4())

    def save_token(self, user_id: str, token: str, device_id: str) -> None:
        hash = hash_with_argon2(token)
        self.redis_session.set(str(user_id) + device_id, hash, ex=timedelta(hours=72))

    def verify_token(self, user_id: int, token: str, device_id: str) -> bool | None:
        hash = self.redis_session.get(str(user_id) + device_id)
        if not hash:
            return None
        str_hash: str = cast(str, hash)
        if verify_hash(token, str_hash):
            self.redis_session.expire(str(user_id) + device_id, timedelta(hours=72))
            return True
        return False


class db_verification:
    async def verify_user_in_conversation(
        self, conversation_id: int, user_id: int, db: AsyncSession
    ) -> bool:
        q = text(
            """
           SELECT * FROM conversation_participants WHERE conversation_id = :ci AND user_id = :ui LIMIT 1 
        """
        )
        return (
            await db.execute(q, {"ci": conversation_id, "ui": user_id})
        ).first() is not None
