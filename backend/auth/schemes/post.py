from pydantic import BaseModel


class SignupSchema(BaseModel):
    username: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str


class RefreshSchema(BaseModel):
    refresh_token: str


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str