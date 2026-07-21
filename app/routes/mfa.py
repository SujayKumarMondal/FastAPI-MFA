from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
import base64
import io
import jwt
import pyotp
import qrcode

from app.auth import get_current_user

from ..core import settings
from ..crud import get_user_by_username
from ..db import get_session
from ..schemas import MFACodeRequest, MFACodeResponse, MFAVerify, MFASetupResponse, MFAVerifyResponse
from ..utils.crypto import encrypt_secret, decrypt_secret

router = APIRouter(prefix="/mfa", tags=["mfa"])


@router.post("/setup", response_model=MFASetupResponse)
def mfa_setup(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    user = current_user

    if user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled for this account")

    if user.mfa_secret:
        try:
            secret = decrypt_secret(user.mfa_secret)
        except RuntimeError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decrypt existing MFA secret")
    else:
        secret = pyotp.random_base32()
        user.mfa_secret = encrypt_secret(secret)
        user.mfa_enabled = False
        session.add(user)
        session.commit()
        session.refresh(user)

    otpauth = pyotp.totp.TOTP(secret).provisioning_uri(name=user.username, issuer_name="FastAPI-MFA")

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(otpauth)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    qr_code_data = base64.b64encode(buffer.read()).decode("utf-8")
    qr_code_data_url = f"data:image/png;base64,{qr_code_data}"

    return MFASetupResponse(
        secret=secret,
        otpauth_url=otpauth,
        qr_code_data_url=qr_code_data_url,
        mfa_enabled=user.mfa_enabled,
    )


@router.post("/code", response_model=MFACodeResponse)
def mfa_code(payload: MFACodeRequest, session: Session = Depends(get_session)):
    try:
        payload_data = jwt.decode(payload.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    token_username = payload_data.get("sub")
    if not token_username or token_username != payload.username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token does not match username")

    user = get_user_by_username(session, payload.username)
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or MFA not configured")

    try:
        secret_plain = decrypt_secret(user.mfa_secret)
    except RuntimeError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decrypt MFA secret")

    if payload.secret != secret_plain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided secret does not match stored secret")

    code = pyotp.TOTP(secret_plain).now()
    return MFACodeResponse(code=code)


@router.post("/verify", response_model=MFAVerifyResponse)
def mfa_verify(payload: MFAVerify, session: Session = Depends(get_session)):
    username = payload.username
    token = str(payload.token).strip()

    try:
        payload_data = jwt.decode(payload.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    token_username = payload_data.get("sub")
    if not token_username or token_username != username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token does not match username")

    user = get_user_by_username(session, username)
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or MFA not configured")

    try:
        secret_plain = decrypt_secret(user.mfa_secret)
    except RuntimeError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decrypt MFA secret")

    totp = pyotp.TOTP(secret_plain)
    ok = totp.verify(token, valid_window=1)
    if ok:
        user.mfa_enabled = True
        session.add(user)
        session.commit()
        session.refresh(user)
        return MFAVerifyResponse(verified=True, mfa_enabled=user.mfa_enabled)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
