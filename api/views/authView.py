from fastapi import APIRouter, HTTPException, Depends, status
from services.tokenService import create_access_token, create_reset_token
from fastapi.responses import JSONResponse
from schemas.userSchema import LoginRequest,  SignUpRequest, ChangePasswordRequest, VerifyLoginOtpRequest, VerifySignupOtpRequest, ForgotPasswordRequest, VerifyForgotPasswordRequest
from schemas.merchantSchema import MerchantResponse
from services import userService, emailService, otpService, tokenService, adminService, merchantService
from database.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import userSchema
import random
import settings

auth_router = APIRouter()


def _user_identity_payload(user):
    payload = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "is_verified": user.is_verified,
    }
    role = getattr(user, "role", None)
    if role is not None:
        payload["role"] = role
    return payload

@auth_router.post("/auth/login")
async def login(data: LoginRequest, session = Depends(get_async_session)):
    otp = str(random.randint(100000, 999999))
    user = await userService.get_user_by_email(session= session, email= data.email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not await userService.check_password(user, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    try:
        await otpService.store_otp(email= data.email, otp=otp)
        await emailService.send_otp_email(data.email, otp)

    except Exception as e:
        return JSONResponse(content={"status": False, "message": f"Error occurred while sending otp: {e}"}, status_code= 400)

    return {"status": True, "message": "Otp sent succesfully"}

@auth_router.post("/auth/signup")
async def signup(data: SignUpRequest, session = Depends(get_async_session)):
    otp = str(random.randint(100000, 999999))

    if await userService.get_user_by_email(session= session, email= data.email):
        raise HTTPException(status_code= 400, detail= "User already exists")

    try:
        await otpService.store_otp(email= data.email, otp=otp)
        await emailService.send_otp_email(data.email, otp)

    except Exception as e:
        return JSONResponse(content={"status": False, "message": f"Error occurred while sending otp: {e}"}, status_code= 400)
    
    return {"status": True, "message": "Otp sent succesfully"}

@auth_router.post("/auth/login/verify-otp")
async def login_otp(data: VerifyLoginOtpRequest, session = Depends(get_async_session)):
    user = await userService.get_user_by_email(session=session, email=data.email)
    
    if not user or not await userService.check_password(user, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_otp = await otpService.get_otp(email=data.email)
    
    if not stored_otp or data.otp != stored_otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP verification failed")

    try:
        await otpService.delete_otp(email=data.email)
    except Exception as e:
        if await otpService.get_otp(email=data.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Otp deletion error")
    admin = await adminService.get_admin_by_email(session=session, email=data.email)
    if admin:
        token = create_access_token({"sub": user.id}, is_admin= True)
    else:
        token = create_access_token({"sub": user.id})
    return {
        "status": True,
        "message": "OTP verified successfully",
        "access_token": token,
        "token_type": "bearer",
        "data": userSchema.UserResponse.model_validate(user)

    }


@auth_router.get("/auth/me")
async def auth_me(current_user=Depends(userService.get_current_user)):
    return {
        "status": True,
        "data": _user_identity_payload(current_user),
    }

@auth_router.post("/auth/signup/verify-otp")
async def signup_otp(data: VerifySignupOtpRequest, session: AsyncSession = Depends(get_async_session)):

    # User should NOT exist yet
    if await userService.get_user_by_email(session=session, email=data.email):
        raise HTTPException(status_code=400, detail="User already exists")

    stored_otp = await otpService.get_otp(email=data.email)

    if not stored_otp or data.otp != stored_otp:
        raise HTTPException(status_code=401, detail="OTP verification failed")

    try:
        await otpService.delete_otp(email=data.email)
    except Exception as e:
        return JSONResponse(
            content={"status": False, "message": f"Error deleting OTP: {e}"},
            status_code=400
        )

    user = await userService.create_user(
        session=session,
        email=data.email,
        name=data.name,
        raw_password=data.password
    )

    token = create_access_token({"sub": user.id})
    return {
        "status": True,
        "message": "OTP verified successfully",
        "access_token": token,
        "token_type": "bearer",
        "data": userSchema.UserResponse.model_validate(user)

    }

@auth_router.post("/auth/change-password")
async def change_password(
    data: ChangePasswordRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(userService.get_current_user)
):
    if not await userService.check_password(current_user, data.current_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    
    await userService.update_password(session=session, user=current_user, raw_password=data.new_password)
    return {"status": True, "message": "Password updated successfully"}

@auth_router.post("/auth/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    session: AsyncSession= Depends(get_async_session)
):
    user = await userService.get_user_by_email(session= session, email= data.email)
    

    if not user:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "User does not exist")
    reset_token = create_reset_token(email= data.email)
    url = f"{settings.FRONTEND_BASE_URL}/reset-password?email={data.email}&code={reset_token}"
        # https://merchant.korapay.com/auth/reset-password?email=chowdome.cu@gmail.com&code=5iiTenNRpMs919svQGs2tZZV6gFKFzabBZtc8VmL9MoT5atP1T&action=password_reset
    try:
        await emailService.send_reset_url(data.email, url)
    except Exception as e:
        return JSONResponse(content={"status": False, "message": f"Error occurred while sending otp: {e}"}, status_code= 400)
    return {"status": True, "message": "Password reset email sent succesfully", "url": url}

@auth_router.post("/auth/forgot-password/verify-reset")
async def forgot_password(
    data: VerifyForgotPasswordRequest,
    session: AsyncSession= Depends(get_async_session)
):
    user = await userService.get_user_by_email(session= session, email= data.email)
    email = tokenService.decode_reset_token(token= data.token)

    if not user:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "User does not exist")
    
    if user.email != email or email is None:
        raise HTTPException(status_code=400, detail="Token verification failed")
    
    user = await userService.update_password(session= session, user= user, raw_password= data.new_password)
    token = create_access_token({"sub": user.id})

    return {
        "status": True,
        "message": "Password updated successfully",
        "access_token": token,
        "token_type": "bearer"
    }

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
_security = HTTPBearer()

@auth_router.get(
    "/auth/validate-key",
    response_model=MerchantResponse,
    summary="Validate an API secret key",
    description=(
        "Validates a merchant's API secret key (aggsk_...) passed as a Bearer token. "
        "Returns the merchant's details if the key is valid."
    ),
    responses={
        200: {
            "description": "Key is valid — merchant details returned",
            "content": {
                "application/json": {
                    "example": {
                        "id": "agg-683c3",
                        "name": "Acme Inc.",
                        "email": "merchant@example.com",
                        "is_verified": False,
                        "is_active": True,
                        "joined_at": "2024-01-01T00:00:00Z",
                        "test_balance": 0.0,
                        "live_balance": 0.0,
                        "percentage_charge": 1.5,
                        "flat_charge": 0.0,
                        "role": None
                    }
                }
            }
        },
        403: {
            "description": "Invalid or malformed API key",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_format": {
                            "summary": "Key format is wrong",
                            "value": {"detail": "Invalid API key format"}
                        },
                        "invalid_key": {
                            "summary": "Key does not match any merchant",
                            "value": {"detail": "Invalid API key"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Merchant associated with key not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Merchant not found"}
                }
            }
        }
    },
    tags=["Auth"]
)
async def validate_key(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    session: AsyncSession = Depends(get_async_session)
):
    token = credentials.credentials
    parts = token.split("_")
    if len(parts) < 4:
        raise HTTPException(status_code=403, detail="Invalid API key format")

    merchant_id = parts[-1]

    is_valid = await tokenService.verify_token(session=session, provided_token=token)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid API key")

    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    return MerchantResponse.model_validate(merchant)
