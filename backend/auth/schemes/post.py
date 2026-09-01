from pydantic import BaseModel, field_validator

class SignupSchema(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_gmail(cls, value: str) -> str:
        if not value.endswith('@gmail.com'):
            raise ValueError('Email @gmail.com bilan tugashi shart!')
        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "string",
                    "first_name": "string",
                    "last_name": "string",
                    "email": "user@gmail.com",
                    "password": "string"
                }
            ]
        }
    }


class LoginSchema(BaseModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@gmail.com",
                    "password": "string"
                }
            ]
        }
    }


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class RefreshSchema(BaseModel):
    refresh_token: str