from typing import AsyncGenerator, Annotated
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED
from db import Session
import security
import models

app = FastAPI(title="msg_api")

token_auth = security.token_auth()

db_auth = security.db_verification()


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
    try:
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
        return JSONResponse(
            status_code=status.HTTP_201_CREATED, content=jsonable_encoder(dict(ret))
        )
    except IntegrityError as e:
        await db.rollback()
        sqlstate = getattr(getattr(e, "orig", None), "sqlstate", None)
        if sqlstate == "23505":
            # Optional: use constraint name to tailor the message
            constraint = getattr(e.orig, "constraint_name", None)
            if constraint == "users_username_key":
                detail = "username already exists"
            elif constraint == "users_mail_key":
                detail = "email already exists"
            else:
                detail = "resource already exists"
            raise HTTPException(status_code=409, detail=detail)
        raise


@app.post("/auth/login")
async def login(
    body: models.LoginModel,
    user_id: Annotated[int, Header(alias="user_id")],
    device_id: Annotated[str, Header(alias="device_id")],
    db: AsyncSession = Depends(get_db),
):
    q = text("SELECT id, password_hash FROM users WHERE id=:id")
    res = (await db.execute(q, {"id": user_id})).mappings().first()

    if not res or not security.verify_hash(body.password, res["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")

    if security.needs_rehash(res["password_hash"]):
        new_hash = security.hash_with_argon2(body.password)
        await db.execute(
            text(
                "UPDATE users SET password_hash=:pw, password_updated_at=now() WHERE id=:id"
            ),
            {"pw": new_hash, "id": user_id},
        )
        await db.commit()

    token = token_auth.generate_token()
    token_auth.save_token(user_id=res["id"], device_id=device_id, token=token)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"msg": "login successful", "token": token},
    )


@app.post("/conversations/new")
async def new_group(
    body: models.NewGroup,
    user_id: Annotated[int, Header(alias="user_id")],
    device_id: Annotated[str, Header(alias="device_id")],
    token: Annotated[str, Header(alias="token")],
    db: AsyncSession = Depends(get_db),
):
    if not token_auth.verify_token(user_id=user_id, device_id=device_id, token=token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "invalid credentials"},
        )
    q = text(
        """
    INSERT INTO conversations (type, created_by, title)
    VALUES (:ty, :cb, :ti)
    RETURNING id
    """
    )
    res = await db.execute(
        q,
        {
            "ty": (1 if len(body.other_participants_ids) <= 2 else 2),
            "cb": int(user_id),
            "ti": body.conversation_title,
        },
    )
    ret = res.mappings().one()

    q2 = text(
        """
        INSERT INTO conversation_participants (conversation_id, user_id, role)
        VALUES (:ci, :ui, :r)
    """
    )
    await db.execute(q2, {"ci": int(ret["id"]), "ui": int(user_id), "r": 3})
    for i in body.other_participants_ids:
        await db.execute(q2, {"ci": int(ret["id"]), "ui": int(i), "r": 1})
    await db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content={"msg": "conversation created"}
    )


@app.get("/conversations")
async def get_all_conversations(
    user_id: Annotated[int, Header(alias="user_id")],
    device_id: Annotated[str, Header(alias="device_id")],
    token: Annotated[str, Header(alias="token")],
    db: AsyncSession = Depends(get_db),
):
    if not token_auth.verify_token(user_id=user_id, device_id=device_id, token=token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "invalid credentials"},
        )
    q = text(
        """
        SELECT id, title, last_written_to FROM conversations WHERE id IN (SELECT conversation_id FROM conversation_participants WHERE user_id=:ui) ORDER BY last_written_to DESC
    """
    )
    res = await db.execute(q, {"ui": int(user_id)})
    ret = res.mappings().all()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"conversations": [(str(i["id"]), str(i["title"])) for i in ret]},
    )


@app.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    user_id: Annotated[int, Header(alias="user_id")],
    device_id: Annotated[str, Header(alias="device_id")],
    token: Annotated[str, Header(alias="token")],
    body: models.SendMessageModel,
    db: AsyncSession = Depends(get_db),
):
    if not token_auth.verify_token(user_id=user_id, device_id=device_id, token=token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if not await db_auth.verify_user_in_conversation(
        user_id=user_id, conversation_id=conversation_id, db=db
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    q = text(
        """
        INSERT INTO messages (conversation_id, sender_id, body)
        VALUES (:ci, :si, :b)
        RETURNING id, body
    """
    )
    res = await db.execute(q, {"ci": conversation_id, "si": user_id, "b": body.message})
    ret = res.mappings().one()
    await db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"id": ret["id"], "msg": ret["body"]},
    )


@app.get("/conversations/{conversation_id}/messages")
async def get_message(
    conversation_id: int,
    user_id: Annotated[int, Header(alias="user_id")],
    device_id: Annotated[str, Header(alias="device_id")],
    token: Annotated[str, Header(alias="token")],
    db: AsyncSession = Depends(get_db),
):
    if not token_auth.verify_token(user_id=user_id, device_id=device_id, token=token):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail={"msg": "invalid credentials"}
        )
    if not await db_auth.verify_user_in_conversation(
        user_id=user_id, conversation_id=conversation_id, db=db
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    q = text(
        """
        SELECT id, body, created_at FROM messages WHERE conversation_id = :ci ORDER BY created_at DESC LIMIT 20
    """
    )
    res = await db.execute(q, {"ci": conversation_id})
    ret = res.mappings().all()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "messages": [
                [str(i["id"]), str(i["body"]), str(i["created_at"])] for i in ret
            ]
        },
    )


@app.get("/")
async def root():
    return "test"
