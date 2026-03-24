import asyncio
from tortoise import Tortoise
from settings import DB_URL

print(f"Using database URL: {DB_URL}")

async def init():
    """Initialize Tortoise ORM and generate database schemas"""
    try:
        await Tortoise.init(
            db_url=DB_URL,  # Ensure DB_URL is correctly set in settings
            modules={"models": ["models.merchant", "models.token", "models.customer", "models.user", "models.transaction", 'aerich.models']},
            use_tz=True,
            timezone='Africa/Lagos'
        )
        print("Connected to the database ✅")

        await Tortoise.generate_schemas(safe=True)  # Create tables
        print("Migrations applied successfully ✅")

    except Exception as e:
        print(f"Error occurred: {e}")
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(init())  # Run the migration script
