from datetime import datetime, timedelta, timezone
import uuid

import pyotp
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from .. import crud, schemas
from ..auth import create_access_token, create_refresh_token, get_current_user, require_roles
from ..core import settings
from ..db import get_session
from ..utils.crypto import decrypt_secret
from ..utils.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])

login_attempts: dict[str, list[datetime]] = {}


def _check_rate_limit(identifier: str) -> None:
    now = datetime.utcnow()
    window = timedelta(minutes=settings.LOGIN_WINDOW_MINUTES)
    attempts = login_attempts.setdefault(identifier, [])
    attempts[:] = [stamp for stamp in attempts if now - stamp < window]
    if len(attempts) >= settings.MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")
    attempts.append(now)


def _clear_rate_limit(identifier: str) -> None:
    login_attempts.pop(identifier, None)


@router.post("/register", response_model=schemas.UserRead)
def register(data: schemas.UserCreate, session: Session = Depends(get_session)):
    existing = crud.get_user_by_username(session, data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    if data.email and crud.get_user_by_email(session, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = crud.create_user(session, data.username, data.password, data.email)
    token = uuid.uuid4().hex
    expires_at = datetime.utcnow() + timedelta(hours=24)
    crud.create_email_verification_token(session, user.id, token, expires_at)
    send_email(
        subject="Verify your account",
        body=f"Use this token to verify your account: {token}",
        to=user.email or user.username,
    )
    return schemas.UserRead.model_validate(user)


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(current_user=Depends(get_current_user)):
    return schemas.UserRead.model_validate(current_user)


@router.patch("/me", response_model=schemas.UserRead)
def update_current_user(
    data: schemas.UserUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if data.email and crud.get_user_by_email(session, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.update_user(session, current_user, email=data.email)
    return schemas.UserRead.model_validate(user)


@router.post("/change-password")
def change_password(
    payload: schemas.ChangePasswordRequest,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not crud.verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    crud.set_password(session, current_user, payload.new_password)
    crud.create_audit_log(session, current_user.id, "change_password")
    return {"detail": "Password updated successfully"}


@router.post("/deactivate")
def deactivate_account(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()
    return {"detail": "Account deactivated"}


@router.post("/delete-account")
def delete_account(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    current_user.is_active = False
    session.delete(current_user)
    session.commit()
    return {"detail": "Account deleted"}


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    mfa_token: str | None = Form(None),
    session: Session = Depends(get_session),
):
    identifier = f"{request.client.host}:{form_data.username}" if request.client else form_data.username
    _check_rate_limit(identifier)

    user = crud.get_user_by_username(session, form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    if user.mfa_enabled:
        if not mfa_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA token required")
        if not user.mfa_secret:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MFA is enabled but secret is missing")
        try:
            secret_plain = decrypt_secret(user.mfa_secret)
        except RuntimeError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decrypt MFA secret")
        totp = pyotp.TOTP(secret_plain)
        if not totp.verify(str(mfa_token).strip(), valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA token")

    access_token_expires = timedelta(minutes=60 * 24 * 7)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)
    crud.create_refresh_token(session, user.id, refresh_token, datetime.utcnow() + refresh_token_expires)
    user.last_login_at = datetime.utcnow()
    session.add(user)
    session.commit()
    _clear_rate_limit(identifier)
    crud.create_audit_log(session, user.id, "login")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(payload: schemas.RefreshTokenRequest, session: Session = Depends(get_session)):
    entry = crud.get_refresh_token(session, payload.refresh_token)
    if not entry or entry.revoked or entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = crud.get_user_by_id(session, entry.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is not active")

    entry.revoked = True
    session.add(entry)
    access_token_expires = timedelta(minutes=60 * 24 * 7)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)
    crud.create_refresh_token(session, user.id, new_refresh_token, datetime.utcnow() + refresh_token_expires)
    session.commit()
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post("/forgot-password")
def forgot_password(payload: schemas.ForgotPasswordRequest, session: Session = Depends(get_session)):
    user = crud.get_user_by_email(session, payload.email)
    if user:
        token = uuid.uuid4().hex
        expires_at = datetime.utcnow() + timedelta(hours=2)
        crud.create_password_reset_token(session, user.id, token, expires_at)
        send_email(
            subject="Reset your password",
            body=f"Use this token to reset your password: {token}",
            to=user.email or user.username,
        )
    return {"detail": "If that email exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(payload: schemas.ResetPasswordRequest, session: Session = Depends(get_session)):
    token_entry = crud.get_password_reset_token(session, payload.token)
    if not token_entry or token_entry.used or token_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = crud.get_user_by_id(session, token_entry.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    crud.set_password(session, user, payload.new_password)
    crud.consume_password_reset_token(session, token_entry)
    return {"detail": "Password reset successful"}


@router.post("/verify-email")
def verify_email(payload: schemas.ResetPasswordRequest, session: Session = Depends(get_session)):
    token_entry = crud.get_email_verification_token(session, payload.token)
    if not token_entry or token_entry.used or token_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user = crud.get_user_by_id(session, token_entry.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    user.updated_at = datetime.utcnow()
    session.add(user)
    crud.consume_email_verification_token(session, token_entry)
    return {"detail": "Email verified successfully"}


@router.get("/admin/users", response_model=schemas.AdminUsersResponse)
def list_admin_users(
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    role: str | None = None,
    current_user=Depends(require_roles("admin")),
    session: Session = Depends(get_session),
):
    users, total = crud.list_users(session, skip=skip, limit=limit, search=search, role=role)
    return {
        "items": [schemas.UserRead.model_validate(user) for user in users],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
