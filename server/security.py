from passlib.context import CryptContext
from typing import Optional
import os
import time
import uuid
import jwt


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=131073,
    argon2__time_cost=3,
    argon2__parallelism=2,
)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hash: str) -> bool:
    return pwd_context.verify(plain, hash)


def needs_rehash(hash: str) -> bool:
    return pwd_context.needs_update(hash)
