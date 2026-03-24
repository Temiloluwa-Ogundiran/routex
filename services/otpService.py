from settings import redis_client
OTP_EXPIRY_IN_SECONDS = 900 #15 mins

async def store_otp(email: str, otp: str, ttl: int = OTP_EXPIRY_IN_SECONDS):
    key = f"otp:{email}"
    await redis_client.set(key, otp, ex=ttl)
    

async def get_otp(email: str) -> str | None:
    """Retrieves the OTP for the given email."""
    key = f"otp:{email}"
    return await redis_client.get(key)

async def delete_otp(email: str):
    """Deletes the OTP (after successful validation)."""
    key = f"otp:{email}"
    await redis_client.delete(key)
