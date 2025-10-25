from pydantic import BaseModel
from typing import List


class CreateUserModel(BaseModel):
    username: str
    display_name: str
    mail: str
    new_password: str


class LoginModel(BaseModel):
    password: str


class NewGroup(BaseModel):
    other_participants_ids: List[str]
    conversation_title: str


class SendMessageModel(BaseModel):
    message: str
