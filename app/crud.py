from sqlmodel import select
from passlib.context import CryptContext

from .models import User

# Use pbkdf2_sha256 to avoid bcrypt 72-byte limit and C-extension issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user_by_username(session, username: str):
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()


def create_user(session, username: str, password: str, email: str | None = None):
    hashed = get_password_hash(password)
    user = User(username=username, hashed_password=hashed, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
