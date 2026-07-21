from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
import pyotp

from .. import crud, schemas
from ..auth import create_access_token, get_current_user
from ..db import get_session
from ..utils.crypto import decrypt_secret

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserRead)
def register(data: schemas.UserCreate, session: Session = Depends(get_session)):
    existing = crud.get_user_by_username(session, data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = crud.create_user(session, data.username, data.password, data.email)
    return schemas.UserRead.from_orm(user)


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(current_user=Depends(get_current_user)):
    return current_user


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    mfa_token: str | None = Form(None),
    session: Session = Depends(get_session),
):
    user = crud.get_user_by_username(session, form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    if user.mfa_enabled:
        if not mfa_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA token required")
        if not user.mfa_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA is enabled but secret is missing")
        try:
            secret_plain = decrypt_secret(user.mfa_secret)
        except RuntimeError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decrypt MFA secret")
        totp = pyotp.TOTP(secret_plain)
        if not totp.verify(str(mfa_token).strip(), valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA token")

    access_token_expires = timedelta(minutes=60 * 24 * 7)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
