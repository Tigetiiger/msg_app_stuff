from pydantic import BaseModel
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db import Session
import security

app = FastAPI(title="msg_api")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as s:
        yield s


class CreateUserIn(BaseModel):
    username: str
    display_name: str | None = None
    mail: str
    new_password: str


@app.post("/users")
async def create_user(body: CreateUserIn, db: AsyncSession = Depends(get_db)):
    q = text(
        """
        INSERT INTO users (username, display_name, mail, password_hash)
        VALUES (:u, :d, :m, :pw)
        RETURNING id, username, display_name, mail, created_at
    """
    )
    password_hash = security.hash_password(body.new_password)
    res = await db.execute(
        q,
        {
            "u": body.username,
            "d": body.display_name,
            "m": body.mail,
            "pw": password_hash,
        },
    )
    ret = res.mappings().one()
    await db.commit()
    return dict(ret)


class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    q = text("SELECT id, password_hash FROM users WHERE username=:u")
    res = (await db.execute(q, {"u": body.username})).mappings().first()

    if not res or not security.verify_password(body.password, res["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")

    if security.needs_rehash(res["password_hash"]):
        new_hash = security.hash_password(body.password)
        await db.execute(
            text(
                "UPDATE users SET password_hash=:pw, password_updated_at=now() WHERE username=:u"
            ),
            {"pw": new_hash, "u": body.username},
        )
        await db.commit()

    return "ok"


print("lolol")


@app.get("/")
async def root():
    return "test"
