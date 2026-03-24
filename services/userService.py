from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from database.models.User import User
from database.models.UserMerchant import UserMerchant
from database.models.Merchant import Merchant
from services import bcryptService
from enums.userEnums import UserRole
from typing import Optional, Union
from settings import PREFIX, ALGORITHM, AUTH_SECRET
import uuid
from sqlalchemy.orm import selectinload
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from services import userService
from database.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
import os
security = HTTPBearer()


async def generate_user_id(session: AsyncSession)->str:
    while True:
        user_id = f'{PREFIX}-{str(uuid.uuid4())[:6]}'
        user = await session.execute(select(User).where(User.id == user_id))
        if not user.scalar_one_or_none():
            return user_id
        
async def check_password(user: User, password: str) -> bool:
    return await bcryptService.check_password(password=password, encrypted=user.password)

async def update_password(session: AsyncSession, user:User, raw_password):
    user.password = await bcryptService.make_password(raw_password)
    session.add(user)
    await session.commit()
    return user
    
async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
    stmt = select(User).options(selectinload(User.merchants)).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).options(selectinload(User.merchants)).where (User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    return user
   


async def create_user(session: AsyncSession, email: str, name: str, raw_password: str, merchant: Merchant= None) -> Optional[User]:
    existing_stmt = select(User).where(User.email == email)
    result = await session.execute(existing_stmt)
    if result.scalar_one_or_none():
        return None
    
    encrypted_password = await bcryptService.make_password(password_string=raw_password)
    user = User(id = await generate_user_id(session), email=email, name=name, password=encrypted_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    if merchant:
        user_merchant = UserMerchant(user_id=user.id, merchant_id=merchant.id, role=UserRole.OWNER.value)
        session.add(user_merchant)
        await session.commit()
    
    return await get_user_by_email(session= session, email= email)

async def soft_delete_user(session: AsyncSession, user_id: str) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound
    
    user.is_active = False
    await session.commit()
    return user

async def add_user_to_merchant(session: AsyncSession, user: User, merchant: Merchant, role: Optional[str] = None) -> User:
    stmt = select(UserMerchant).where(UserMerchant.merchant_id == merchant.id)
    result = await session.execute(stmt)
    existing_user_merchants = result.scalars().all()

    if role and not UserRole.is_valid(role):
        raise ValueError("Invalid role")
    if not role:
        role = UserRole.ADMIN.value
        # pass
    if len(existing_user_merchants) == 0:
        role = UserRole.OWNER.value
    
    # role = 'admin'
    user_merchant = UserMerchant(user_id=user.id, merchant_id=merchant.id, role=role)
    session.add(user_merchant)
    await session.commit()

    return await get_user_by_id(session= session, user_id= user.id)

async def set_user_role(session: AsyncSession, user: User, merchant: Merchant, role: str) -> UserMerchant:
    if UserRole.is_valid(role):
        raise ValueError("Invalid role")

    stmt = select(UserMerchant).where(UserMerchant.user_id == user.id, UserMerchant.merchant_id == merchant.id)
    result = await session.execute(stmt)
    user_merchant = result.scalar_one_or_none()
    if not user_merchant:
        raise NoResultFound

    user_merchant.role = role
    await session.commit()
    return await get_user_by_id(session= session, user_id= user.id)

async def get_user_role(session: AsyncSession, user: User, merchant: Merchant) -> str:
    stmt = select(UserMerchant.role).where(
        UserMerchant.user_id == user.id,
        UserMerchant.merchant_id == merchant.id
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    return role

async def get_merchants(session: AsyncSession, user: User) -> list[Merchant]:
    stmt = select(Merchant).join(UserMerchant).where(UserMerchant.user_id == user.id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def user_in_merchant(user: User, merchant: Merchant, session: AsyncSession)->bool:
    user_merchant = await session.execute(select(UserMerchant).where(UserMerchant.user == user, UserMerchant.merchant == merchant))
    if  user_merchant.scalar_one_or_none():
        return True
    return  False

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):

    token = credentials.credentials

    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[ALGORITHM], options={"verify_exp": True})
        print(f"jwt payload: {payload}")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403, detail="Invalid token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=403, detail= f"Error occurred with token validation : {e}")

    user = await userService.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User not accessible")
    return user


async def get_current_user_ws(websocket: WebSocket, session: AsyncSession) -> User | None:
    print("In ws auth")
    auth_header = websocket.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        await websocket.close(code=1008, reason="Authorization missing or malformed")
        return

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[ALGORITHM], options={"verify_exp": True})
        print(f"jwt payload: {payload}")
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return

    except ExpiredSignatureError:
        await websocket.close(code=4003, reason="Token expired")
        return
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return
    except Exception as e:
        await websocket.close(code=1008, reason=f"Token validation error: {e}")
        return

    user = await userService.get_user_by_id(session=session, user_id=user_id)
    if not user:
        await websocket.close(code=1008, reason="User not found")
        return
    if not user.is_active:
        await websocket.close(code=4003, reason="User is inactive")
        return

    return user