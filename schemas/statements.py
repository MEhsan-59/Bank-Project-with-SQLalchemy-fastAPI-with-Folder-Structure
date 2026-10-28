from datetime import datetime

from pydantic import BaseModel


class TransactionItem(BaseModel):
    model_config = {"from_attributes": True}

    type: str
    amount: int
    balance_after: int
    related_account: int | None
    created_at: datetime | None


class StatementResponse(BaseModel):
    transactions: list[TransactionItem]
