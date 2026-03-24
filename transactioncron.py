import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from services import merchantService, tokenService, userService, transactionService
from database.session import get_async_session  # or your session maker
from database.models.Merchant import Merchant
from database.models.Transaction import Transaction
from services.tokenService import create_merchant_token  # example operation
from services.relayService import create_merchant_application
from services.tokenService import create_access_token
from enums import transactionEnums
from datetime import timedelta, datetime,timezone

# async def processn_all_merchants():
#     async for session in get_async_session():  # properly getting a session instance
#   # or get_async_session() if it's a callable
#         merchant = await merchantService.get_by_id_or_email(session= session, email= "chowdome@gmail.com")
#         # merchant.live_webhook_url = ""
#         # merchant.test_webhook_url = ""
#         merchant.is_verified = True
#         merchant = await merchantService.save_merchant(session= session, merchant= merchant)
#         token = await tokenService.create_merchant_token(session= session, type= "live", merchant= merchant)
#         return token

async def process_all_transactions():
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    async for session in get_async_session():
        try:
            stmt = (
                update(Transaction)
                .where(
                    Transaction.status == transactionEnums.TransactionStatus.PENDING,
                    Transaction.created_at <= one_hour_ago
                )
                .values(status=transactionEnums.TransactionStatus.ABANDONED)
                .execution_options(synchronize_session=False)  # No ORM state tracking needed
            )
            await session.execute(stmt)
            await session.commit()

        except Exception as e:
            await session.rollback()
            print(f"Error processing transactions: {e}")

asyncio.run(process_all_transactions())      
       
# async def generate_auth_token():
#   async for session in get_async_session():
#     user= await userService.get_user_by_email(session= session, email= "chowdome.cu@gmail.com")
#     token = create_access_token({"sub": user.id})
#     print(token)
     
   


