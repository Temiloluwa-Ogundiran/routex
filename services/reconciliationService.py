from database.models.Transaction import Transaction


def mark_for_reconciliation(transaction: Transaction, reason: str) -> Transaction:
    details = dict(transaction.details or {})
    details["reconciliation_required"] = True
    details["reconciliation_reason"] = reason
    transaction.details = details
    return transaction
