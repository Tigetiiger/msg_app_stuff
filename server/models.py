from pydantic import BaseModel
from typing import List


class CreateUserModel(BaseModel):
    username: str
    display_name: str
    mail: str
    new_password: str


class LoginModel(BaseModel):
    username: str
    password: str
    device_id: str


class NewGroup(BaseModel):
    user_id: str
    device_id: str
    token: str
    other_participants_ids: List[str]
    conversation_title: str


class GetConversationsModel:
    user_id: str
    device_id: str
    token: str
