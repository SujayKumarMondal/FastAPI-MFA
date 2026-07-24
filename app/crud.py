import hashlib
from datetime import datetime, timedelta
from sqlmodel import select
from passlib.context import CryptContext

from .models import AuditLog, EmailVerificationToken, PasswordResetToken, RefreshToken, User

# Use pbkdf2_sha256 to avoid bcrypt 72-byte limit and C-extension issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user_by_username(session, username: str):
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()


def get_user_by_email(session, email: str):
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_id(session, user_id: int):
    return session.get(User, user_id)


def create_user(session, username: str, password: str, email: str | None = None, role: str = "user"):
    hashed = get_password_hash(password)
    user = User(username=username, hashed_password=hashed, email=email, role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session, user: User, **updates):
    for key, value in updates.items():
        if hasattr(user, key):
            setattr(user, key, value)
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def set_password(session, user: User, password: str):
    user.hashed_password = get_password_hash(password)
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_users(session, skip: int = 0, limit: int = 20, search: str | None = None, role: str | None = None):
    statement = select(User)
    if search:
        search_term = f"%{search.lower()}%"
        statement = statement.where((User.username.ilike(search_term)) | (User.email.ilike(search_term)))
    if role:
        statement = statement.where(User.role == role)
    statement = statement.offset(skip).limit(limit)
    users = session.exec(statement).all()
    total = session.exec(select(User).where(User.id.is_not(None))).all()
    return users, len(total)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(session, user_id: int, token: str, expires_at: datetime):
    token_entry = RefreshToken(token_hash=hash_token(token), user_id=user_id, expires_at=expires_at)
    session.add(token_entry)
    session.commit()
    session.refresh(token_entry)
    return token_entry


def get_refresh_token(session, token: str):
    statement = select(RefreshToken).where(RefreshToken.token_hash == hash_token(token))
    return session.exec(statement).first()


def revoke_refresh_tokens(session, user_id: int):
    statement = select(RefreshToken).where(RefreshToken.user_id == user_id)
    entries = session.exec(statement).all()
    for entry in entries:
        entry.revoked = True
    session.commit()


def create_password_reset_token(session, user_id: int, token: str, expires_at: datetime):
    token_entry = PasswordResetToken(token_hash=hash_token(token), user_id=user_id, expires_at=expires_at)
    session.add(token_entry)
    session.commit()
    session.refresh(token_entry)
    return token_entry


def get_password_reset_token(session, token: str):
    statement = select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(token))
    return session.exec(statement).first()


def consume_password_reset_token(session, token_entry: PasswordResetToken):
    token_entry.used = True
    session.add(token_entry)
    session.commit()


def create_email_verification_token(session, user_id: int, token: str, expires_at: datetime):
    token_entry = EmailVerificationToken(token_hash=hash_token(token), user_id=user_id, expires_at=expires_at)
    session.add(token_entry)
    session.commit()
    session.refresh(token_entry)
    return token_entry


def get_email_verification_token(session, token: str):
    statement = select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hash_token(token))
    return session.exec(statement).first()


def consume_email_verification_token(session, token_entry: EmailVerificationToken):
    token_entry.used = True
    session.add(token_entry)
    session.commit()


def create_audit_log(session, user_id: int | None, action: str, details: str | None = None):
    log = AuditLog(user_id=user_id, action=action, details=details)
    session.add(log)
    session.commit()
    return log
