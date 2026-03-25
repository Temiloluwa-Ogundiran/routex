import os
import logging
from fastapi import FastAPI
from dotenv import load_dotenv
import redis.asyncio as redis


from tortoise.contrib.fastapi import register_tortoise
from tortoise import Tortoise
import pytz
app = FastAPI()
load_dotenv()
PREFIX = 'agg'
logging.basicConfig(level=logging.INFO)
DB_URL = os.getenv('DB_URL')
AGG_SECRET = os.getenv('AGG_SECRET')
# Set Nigerian Timezone (WAT)
NIGERIA_TZ = pytz.timezone("Africa/Lagos")

AGG_EMAIL = "auth.xaggregator@gmail.com"

PROXY_PASSWORD= os.getenv('PROXY_PASSWORD')
PROXY_URL= os.getenv('PROXY_URL')
PROXY_USERNAME= os.getenv('PROXY_USERNAME')

KORA_SECRET = os.getenv('KORA_SECRET_KEY')
KORA_LIVE_SECRET_KEY = os.getenv("KORA_LIVE_SECRET_KEY")

PAYSTACK_SECRET = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_LIVE_SECRET_KEY = os.getenv("PAYSTACK_LIVE_SECRET_KEY")

BASQET_SECRET = os.getenv("BASQET_SECRET")
BASQET_LIVE_SECRET = os.getenv("BASQET_LIVE_SECRET")

RELAY_TOKEN = os.getenv("RELAY_TOKEN")

FLTW_SECRET_KEY = os.getenv('FLTW_SECRET_KEY')
FLTW_SECRET_HASH = os.getenv("FLTW_SECRET_HASH")
INTERSWITCH_MERCHANT_CODE = os.getenv("INTERSWITCH_MERCHANT_CODE")
INTERSWITCH_PAY_ITEM_ID = os.getenv("INTERSWITCH_PAY_ITEM_ID")
INTERSWITCH_CLIENT_ID = os.getenv("INTERSWITCH_CLIENT_ID")
INTERSWITCH_SECRET_KEY = os.getenv("INTERSWITCH_SECRET_KEY")

SERVER_URL = os.getenv("SERVER_URL")
V1_API_URL = "https://api.xoropay.com"

IS_V1 = SERVER_URL == V1_API_URL

REDIS_URL = os.getenv("REDIS_URL")

TWILLO_AUTH_TOKEN = os.getenv("TWILLO_AUTH_TOKEN")

ALGORITHM = "HS256"
AUTH_SECRET= os.getenv("AUTH_SECRET")
ACCESS_TOKEN_EXPIRE_MINUTES= 60

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
AUTH_EMAIL = os.getenv("AUTH_EMAIL")
RECEIPT_EMAIL = os.getenv("RECEIPT_EMAIL")


redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,  # auto-decodes to str
)

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://www.xoropay.com")
TEMP_PAYOUT_FEE = 60
CHECKOUT_URL = os.getenv("CHECKOUT_URL", "https://checkout.xoropay.com")
MAX_WS_LIFETIME = 1800 #30 MINUTES
