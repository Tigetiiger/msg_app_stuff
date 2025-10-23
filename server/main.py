from typing import AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db import Session
import security
import models

app = FastAPI(title="msg_api")

token_auth = security.token_auth()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as s:
        yield s


@app.post("/users")
async def create_user(body: models.CreateUserModel, db: AsyncSession = Depends(get_db)):
    q = text(
        """
        INSERT INTO users (username, display_name, mail, password_hash)
        VALUES (:u, :d, :m, :pw)
        RETURNING id, username, display_name, mail, created_at
    """
    )
    password_hash = security.hash_with_argon2(body.new_password)
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


@app.post("/auth/login")
async def login(body: models.LoginModel, db: AsyncSession = Depends(get_db)):
    q = text("SELECT id, password_hash FROM users WHERE username=:u")
    res = (await db.execute(q, {"u": body.username})).mappings().first()

    if not res or not security.verify_hash(body.password, res["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")

    if security.needs_rehash(res["password_hash"]):
        new_hash = security.hash_with_argon2(body.password)
        await db.execute(
            text(
                "UPDATE users SET password_hash=:pw, password_updated_at=now() WHERE username=:u"
            ),
            {"pw": new_hash, "u": body.username},
        )
        await db.commit()

    token = token_auth.generate_token()
    token_auth.save_token(user_id=res["id"], device_id=body.device_id, token=token)
    return {"msg": "login successful", "token": token}


print("lolol")


@app.get("/")
async def root():
    return "test"
