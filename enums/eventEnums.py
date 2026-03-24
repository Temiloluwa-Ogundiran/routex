from enum import StrEnum

class EventType(StrEnum):
    CHARGE_SUCCESS = "charge.success"
    CHARGE_FAILED = "charge.failed"
    TRANSFER_SUCCESS = "transfer.success"
    TRANSFER_FAILED = "transfer.failed"
    