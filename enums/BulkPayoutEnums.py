from enum import StrEnum

class BulkPayoutStatus(StrEnum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    PARTIAL = "partial"

class BulkPayoutTransactionKeys(StrEnum):
    TXN_ID = "txn_id"
    STATUS = "status"
    MESSAGE = "message"
    TXN_STATUS = "txn_status"
    TXN_MESSAGE = "txn_message"
    HTTP_STATUS = "http_status"

class BulkPayoutStatusMessage(StrEnum):
    PENDING = "Transaction has been queued and is still being processed"
    SUCCESS = "Transaction has been successfully completed"
    FAILED = "Transaction failed"

class BulkPayoutMode(StrEnum):
    LIVE = 'live'
    TEST = 'test'