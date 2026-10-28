from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models import Account
from repositories.account_repository import AccountRepository
from repositories.transaction_repository import TransactionRepository
from schemas.transactions import (
    BalanceResponse,
    DepositRequest,
    DepositResponse,
    TransferConfirmRequest,
    TransferPreviewRequest,
    TransferPreviewResponse,
)
from services.transaction_service import TransactionService
from utils.dependencies import get_current_account
from utils.exceptions import ReceiverNotFound

router = APIRouter()


def get_transaction_service(
    db: Session = Depends(get_db),
) -> TransactionService:
    return TransactionService(
        TransactionRepository(db),
        AccountRepository(db),
    )


@router.get("/check_balance", response_model=BalanceResponse)
def check_balance(
    account: Account = Depends(get_current_account),
) -> BalanceResponse:
    return BalanceResponse(success=True, balance=account.balance)


@router.post("/deposit", response_model=DepositResponse)
def deposit(
    data: DepositRequest,
    account: Account = Depends(get_current_account),
    service: TransactionService = Depends(get_transaction_service),
) -> DepositResponse:
    balance = service.deposit(account, data.amount)
    if balance is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    return DepositResponse(
        success=True,
        message=f"{data.amount} successfully deposited.",
        balance=balance,
    )


@router.post("/send_money/preview", response_model=TransferPreviewResponse)
def preview_transfer(
    data: TransferPreviewRequest,
    account: Account = Depends(get_current_account),
    service: TransactionService = Depends(get_transaction_service),) -> TransferPreviewResponse:
    transfer = service.preview_transfer(
        account, data.receiver_account_no, data.amount
    )
    receiver = service.accounts.get_by_account_no(transfer.receiver_account_no)
    if receiver is None:
        raise ReceiverNotFound()
    return TransferPreviewResponse(
        receiver_account_no=receiver.account_no,
        receiver_name=receiver.user_name,
        amount=transfer.amount,
        transaction_id=transfer.transfer_id,
    )
@router.post("/send_money/confirm")
def confirm_transfer(
    data: TransferConfirmRequest,
    account: Account = Depends(get_current_account),
    service: TransactionService = Depends(get_transaction_service),
) -> dict[str, bool | str]:
    result = service.confirm_transfer(account, data.transaction_id)
    if result == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Transaction not found or already used.",
        )
    if result == "forbidden":
        raise HTTPException(
            status_code=403,
            detail="This transaction does not belong to you.",
        )
    if result == "account_frozen":
        raise HTTPException(
            status_code=403,
            detail="Your account is frozen. Please contact the admin.",
        )
    if result == "receiver_not_found":
        raise HTTPException(status_code=404, detail="Receiver account not found.")
    if result == "insufficient_balance":
        raise HTTPException(status_code=400, detail="Insufficient balance.")
    return {"success": True, "message": "Money transferred successfully."}