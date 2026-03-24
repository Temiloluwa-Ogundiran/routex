from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from enums import transactionEnums

class Customer(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class Destination(BaseModel):
    bank_code: str = Field(..., example="044", description="Bank code of the destination bank")
    account_number: str = Field(..., example="0123456789", description="Destination bank account number")


    
class InitializeTransactionRequest(BaseModel):
    customer: Customer
    amount: float
    currency: transactionEnums.TransactionCurrency = Field(description="Currency in lower case")
    reference: str
    redirect_url: Optional[str] = None
    notification_url: Optional[str] = None
    narration: Optional[str] = None
    mode: Optional[transactionEnums.TransactionChannel] = None
    metadata: Optional[dict] = None



class InitializeTransactionResponse(BaseModel):
    status: bool = Field(..., example=True, description="Indicates if the transaction initialization was successful")
    message: str = Field(..., example="Charge created successfully", description="Human-readable message")
    reference: Optional[str] = Field(None, example="TXN_123456", description="Transaction reference")
    checkout_url: Optional[str] = Field(None, example="https://checkout.payment.com/tx/123", description="URL for customer to complete payment")


class InitializeErrorResponse(BaseModel):
    # status_code: int = Field(..., example=400, description="HTTP status code")
    detail: str = Field(..., example="Error message", description="Error message describing what went wrong")



# --- Request schema ---
class PayoutRequest(BaseModel):
    amount: float = Field(..., example=5000.0, description="Amount to payout")
    currency: str = Field(..., example="NGN", description="Currency code in ISO format")
    reference: str = Field(..., example="PAYOUT_123456", description="Unique payout reference")
    customer: Customer = Field(..., description="Customer details")
    destination: Destination = Field(..., description="Destination bank details")
    metadata: Optional[Dict[str, Any]] = Field(None, example={"order_id": "123"}, description="Custom metadata for the payout")
    narration: Optional[str] = Field(None, example="Payment for order 123", description="Optional narration for the payout")

# --- Success response schema ---
class PayoutResponse(BaseModel):
    status: bool = Field(..., example=True, description="Indicates if the payout was successful")
    message: str = Field(..., example="Payout processed successfully", description="Human-readable message")
    data: Dict[str, Any] = Field(
        ..., 
        example={
            "amount": 5000.0,
            "fee": 50.0,
            "reference": "PAYOUT_123456",
            "customer": {
                "email": "customer@example.com",
                "name": "John Doe"
            }
        },
        description="Details of the payout including fees and customer information"
    )

# --- Error response schema ---
class PayoutErrorResponse(BaseModel):
    status_code: int = Field(..., examples=[400, 403, 404, 422], description="HTTP status code")
    detail: str = Field(..., example="Error message", description="Error message describing what went wrong")
# class VerifyTransactionResponse(BaseModel):


    email: str = Field(..., example="customer@example.com", description="Customer's email address")

class TransactionData(BaseModel):
    domain: str = Field(..., example="TEST", description="Transaction domain/mode")
    type: str = Field(..., example="PAYMENT", description="Transaction type")
    amount: float = Field(..., example=5000.0, description="Transaction amount")
    fee: float = Field(..., example=50.0, description="Transaction fee")
    currency: str = Field(..., example="NGN", description="Currency code in ISO format")
    narration: Optional[str] = Field(None, example="Payment for order 123", description="Optional narration")
    metadata: Optional[Dict[str, Any]] = Field(None, example={"order_id": "123"}, description="Custom metadata")
    created_at: str = Field(..., example="2025-09-17T12:00:00Z", description="Timestamp when transaction was created")
    updated_at: str = Field(..., example="2025-09-17T12:05:00Z", description="Timestamp when transaction was last updated")
    customer: Customer = Field(..., description="Customer details")

class VerifyTransactionResponse(BaseModel):
    status: bool = Field(..., example=True, description="Indicates if verification was successful")
    message: str = Field(..., example="Verification successful", description="Human-readable message")
    data: TransactionData = Field(..., description="Details of the verified transaction")

# --- Error response ---
class VerifyErrorResponse(BaseModel):
    status_code: int = Field(..., example=404, description="HTTP status code")
    detail: str = Field(..., example="Transaction not found", description="Error message describing what went wrong")

    class Config:
        schema_extra = {
            "examples": {
                "400": {
                    "summary": "Bad request / verification failed",
                    "value": {
                        "status_code": 400,
                        "detail": "Verification failed: invalid reference format"
                    }
                },
                "403": {
                    "summary": "Invalid payment secret key",
                    "value": {
                        "status_code": 403,
                        "detail": "Invalid payment secret key provided"
                    }
                },
                "404_merchant": {
                    "summary": "Merchant not found",
                    "value": {
                        "status_code": 404,
                        "detail": "Merchant not found"
                    }
                },
                "404_transaction": {
                    "summary": "Transaction not found",
                    "value": {
                        "status_code": 404,
                        "detail": "Transaction not found"
                    }
                },
                "404_test_mode": {
                    "summary": "Test domain cannot see live transaction",
                    "value": {
                        "status_code": 404,
                        "detail": "Test domain can only see transactions in test mode"
                    }
                }
            }
        }