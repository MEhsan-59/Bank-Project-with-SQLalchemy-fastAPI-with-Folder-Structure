from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    success: bool
    balance: int


class DepositRequest(BaseModel):
    amount: int = Field(..., gt=0, le=10000)


class DepositResponse(BaseModel):
    success: bool
    message: str
    balance: int


class TransferPreviewRequest(BaseModel):
    receiver_account_no: str = Field(..., min_length=6, max_length=20)
    amount: int = Field(..., gt=0)


class TransferPreviewResponse(BaseModel):
    receiver_account_no: str
    receiver_name: str
    amount: int
    transaction_id: str


class TransferConfirmRequest(BaseModel):
    transaction_id: str = Field(..., min_length=36, max_length=36)
