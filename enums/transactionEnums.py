from enum import StrEnum

class TransactionStatus(StrEnum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    ABANDONED = 'abandoned'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_

class TransactionType(StrEnum):
    CREDIT = 'credit'
    DEBIT = 'debit' 

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_
    
class TransactionChannel(StrEnum):
    CARD = 'card'
    TRANSFER = 'bank_transfer'
    CRYPTO = "crypto"
    MOBILE_MONEY = "mobile_money"
    # USSD = 'ussd'
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_
class TransactionProcessor(StrEnum):
    FLUTTERWAVE = 'fltw'
    KORA = 'kora'
    PAYSTACK = 'pstk'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_
# Kenya (KES), Ghana (GHS), Cameroon (XAF), Ivory Coast (XOF), Egypt (EGP) and Tanzania (TZS).    
class TransactionCurrency(StrEnum):
    NIGERIA = "NGN"
    KENYA = 'KES'
    GHANA = 'GES'
    CAMEROON = 'XAF'
    IVORY_COAST = "XOF"
    EGYPT = "EGP"
    TANZANIA = 'TZS'
    BITCOIN = "BTC"
    ETHEREUM = "ETH"
    TETHER = "USDT"
    SOLANA = "SOL"
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_
    
class GroupBy(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"