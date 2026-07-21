from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    mfa_enabled: bool
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


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
