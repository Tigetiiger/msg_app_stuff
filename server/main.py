from pydantic import BaseModel
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db import Session


app = FastAPI(title="msg_api")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as s:
        yield s


class CreateUserIn(BaseModel):
    username: str
    display_name: str | None = None


@app.post("/users")
async def create_user(body: CreateUserIn, db: AsyncSession = Depends(get_db)):
    q = text(
        """
        INSERT INTO users (username, display_name)
        VALUES (:u, :d)
        RETURNING id, username, display_name, created_at
    """
    )
    res = await db.execute(q, {"u": body.username, "d": body.display_name})
    ret = res.mappings().one()
    await db.commit()
    return dict(ret)


print("lolol")


@app.get("/")
async def root():
    return "test"
