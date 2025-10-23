from pydantic import BaseModel


class CreateUserModel(BaseModel):
    username: str
    display_name: str
    mail: str
    new_password: str


class LoginModel(BaseModel):
    username: str
    password: str
    device_id: str
