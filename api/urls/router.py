from fastapi import APIRouter
# from api.views.transactionView import transaction_router
# from api.views.merchantView import merchant_router
from settings import IS_V1
from api.views.userView import user_router
from api.views.merchantView import merchant_router
from api.views.transactionView import transaction_router
from api.views.authView import auth_router
from api.views.adminView import admin_router
from api.views.socketView import socket_router
from api.views.linkView import link_router
from api.views.docs import docs_router
from api.views.categoryView import category_router, beneficiary_router
from api.views.apiCheckoutView import checkout_router
from api.views.walletView import wallet_router
from api.views.analyticsView import analytics_router
from api.v1 import initialize, webhooks, payout, verify_transaction, banks, cryptos
router = APIRouter()
if not IS_V1: #Dashboard only paths
    router.include_router(docs_router)
    router.include_router(auth_router, tags=["Auth"])
    router.include_router(admin_router, tags= ['Admin'])
    router.include_router(user_router, prefix="", tags=["Users"])
    router.include_router(merchant_router, tags= ['Merchants'])
    router.include_router(wallet_router, tags=['Wallets'])
    router.include_router(analytics_router, tags=['Analytics'])
    router.include_router(link_router)
    router.include_router(category_router, tags=['Payout categories'])
    router.include_router(beneficiary_router, tags= ['Payout beneficiaries'])
    router.include_router(transaction_router, tags= ['Transactions'])
    router.include_router(socket_router, tags= ['websockets'])

router.include_router(initialize.initialize_router, tags = ['V1'])
router.include_router(payout.payout_router, tags = ['V1'])
router.include_router(verify_transaction.verify_router, tags=['V1'])
router.include_router(banks.bank_router, tags=['V1'])
router.include_router(cryptos.crypto_router, tags= ['V1'])
router.include_router(checkout_router, tags= ['V2 Checkout'])
router.include_router(webhooks.webhook_router, tags= ['Webhooks'], include_in_schema= False)
router.include_router(webhooks.webhook_util_router, tags= ['Webhooks'])