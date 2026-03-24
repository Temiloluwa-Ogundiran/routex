import base64
import os
from cryptography.fernet import Fernet
from settings import AGG_SECRET, PREFIX
from database.models.Merchant import Merchant
from database.models.Token import Token
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Union
from enums import tokenEnums
from datetime import timedelta
from datetime import datetime, timezone
from jose import JWTError, jwt
from typing import Optional
import settings

cipher_suite = Fernet(AGG_SECRET)


async def generate_token(session: AsyncSession, merchant: Merchant, type: str) -> tuple[str, str]:
    secret_token, public_token = os.urandom(32).hex(), os.urandom(32).hex()

    encrypted_secret_token = cipher_suite.encrypt(secret_token.encode()).decode()
    encrypted_public_token = cipher_suite.encrypt(public_token.encode()).decode()

    token = Token(merchant_id=merchant.id, secret_key=encrypted_secret_token, public_key=encrypted_public_token, type=type)
    session.add(token)
    await session.commit()

    secret_string = f"{PREFIX}sk_{type}_{secret_token}_{merchant.id}"
    public_string = f"{PREFIX}pk_{type}_{public_token}_{merchant.id}"
    return secret_string, public_string

async def get_raw_tokens(session: AsyncSession, token: Token) -> tuple[str, str]:
    await session.refresh(token)
    merchant_id = token.merchant_id
    secret_string = f"{PREFIX}sk_{token.type}_{cipher_suite.decrypt(token.secret_key.encode()).decode()}_{merchant_id}"
    public_string = f"{PREFIX}pk_{token.type}_{cipher_suite.decrypt(token.public_key.encode()).decode()}_{merchant_id}"
    return secret_string, public_string

async def create_merchant_token(session: AsyncSession, merchant: Merchant, type: str = 'test') -> tuple[str, str]:
    if not tokenEnums.TokenMode.is_valid(type):
        raise ValueError("Wrong token type specified")

    if not merchant.is_verified and type == tokenEnums.TokenMode.LIVE.value:
        raise Exception("Merchant is not verified")

    await delete_token(session= session, merchant= merchant, type= type)
    return await generate_token(session, merchant, type)

async def verify_token(session: AsyncSession, provided_token: str) -> bool:
    try:
        parts = provided_token.split("_")
        if len(parts) < 4:
            return False

        token_mode, merchant_id = parts[1], parts[-1]
        if not tokenEnums.TokenMode.is_valid(token_mode):
            return False

        stmt = select(Token).where(Token.merchant_id == merchant_id, Token.type == token_mode)
        result = await session.execute(stmt)
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            return False

        secret_token, public_token = await get_raw_tokens(session, token_obj)
        return provided_token in [secret_token, public_token]

    except Exception as e:
        raise ValueError(f"Token verification failed: {e}")

async def get_merchant_tokens(session: AsyncSession, merchant: Merchant):
    stmt_test = select(Token).where(Token.merchant_id == merchant.id, Token.type == 'test')
    stmt_live = select(Token).where(Token.merchant_id == merchant.id, Token.type == 'live')

    test_token = (await session.execute(stmt_test)).scalar_one_or_none()
    live_token = (await session.execute(stmt_live)).scalar_one_or_none()

    raw_test_tokens = await get_raw_tokens(session, test_token) if test_token else (None, None)
    raw_live_tokens = await get_raw_tokens(session, live_token) if live_token else (None, None)

    return {
        "live": {
            "secret": raw_live_tokens[0],
            "public": raw_live_tokens[1]
        },
        "test": {
            "secret": raw_test_tokens[0],
            "public": raw_test_tokens[1]
        }
    }

async def delete_token(session: AsyncSession, merchant: Merchant, type: str) -> bool:
    """
    Deletes a token for a given merchant and type.

    Returns:
        bool: True if a token was deleted, False otherwise.
    """
    if not tokenEnums.TokenMode.is_valid(type):
        raise ValueError("Wrong token type specified")

    stmt = delete(Token).where(Token.merchant_id == merchant.id, Token.type == type)
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0

async def get_token_obj(session: AsyncSession, merchant: Merchant, mode: str)->Token:
    stmt = select(Token).where(Token.merchant_id == merchant.id, Token.type == mode)
    token = (await session.execute(stmt)).scalar_one_or_none()
    return token



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, is_admin:bool = False):
    to_encode = data.copy()
    if is_admin:
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes= 5 * 60))
    else:
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.AUTH_SECRET, algorithm=settings.ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.AUTH_SECRET, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    
RESET_URL_TTL_IN_SECONDS = 900
def create_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_URL_TTL_IN_SECONDS/60)
    payload = {"sub": email, "exp": expire, "scope": "reset_password"}
    return jwt.encode(payload, settings.AUTH_SECRET, algorithm= settings.ALGORITHM)

def decode_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.AUTH_SECRET, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != "reset_password":
            return None
        return payload.get("sub")  # email
    except JWTError:
        return None
