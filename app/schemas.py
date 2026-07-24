from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class UserUpdate(BaseModel):
    email: Optional[str] = None


class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    mfa_enabled: bool
    role: str
    email_verified: bool
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class MFAVerify(BaseModel):
    username: str
    access_token: str
    token: str


class MFACodeRequest(BaseModel):
    username: str
    access_token: str
    secret: str


class MFACodeResponse(BaseModel):
    code: str


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_data_url: str
    mfa_enabled: bool = False
    model_config = ConfigDict(from_attributes=True)


class MFAVerifyResponse(BaseModel):
    verified: bool
    mfa_enabled: bool


class AdminUsersResponse(BaseModel):
    items: list[UserRead]
    total: int
    skip: int
    limit: int
