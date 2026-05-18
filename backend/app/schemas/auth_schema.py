# app/schemas/auth_schema.py
from pydantic import BaseModel, model_validator


class LoginRequest(BaseModel):
    login: str | None = None
    email: str | None = None
    password: str

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.login and not self.email:
            raise ValueError("Informe login ou e-mail.")
        return self


class TokenResponse(BaseModel):
    id: int
    name: str
    login: str
    email: str
    role: str
    active: bool
    token: str
    access_token: str
    token_type: str = "bearer"
    expiresAt: str | None = None


class AuthenticatedUserResponse(BaseModel):
    id: int
    name: str
    login: str
    email: str
    role: str
    active: bool
    perfil: str


class LogoutResponse(BaseModel):
    message: str
