from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from models import Account, PendingTransfer, Transaction


class TransactionRepository:
    
    def __init__(self, db: Session):
        self.db = db

    def add_pending_transfer(
        self,
        sender_user_id: str,
        receiver_account_no: int,
        amount: int,
    ) -> PendingTransfer:
        transfer = PendingTransfer(
            transfer_id=str(uuid4()),
            sender_user_id=sender_user_id,
            receiver_account_no=receiver_account_no,
            amount=amount,
        )
        self.db.add(transfer)
        self.db.flush()
        self.commit()
        return transfer

    def get_pending_transfer(self, transfer_id: str) -> PendingTransfer | None:
        return (
            self.db.query(PendingTransfer)
            .filter(PendingTransfer.transfer_id == transfer_id)
            .first()
        )

    def delete_pending_transfer(self, transfer: PendingTransfer) -> bool:
        result = self.db.execute(
            delete(PendingTransfer).where(
                PendingTransfer.transfer_id == transfer.transfer_id,
                PendingTransfer.sender_user_id == transfer.sender_user_id,
            )
        )
        return result.rowcount == 1

    def debit(self, user_id: str, amount: int) -> bool:
        result = self.db.execute(
            update(Account)
            .where(
                Account.user_id == user_id,
                Account.freeze.is_(False),
                Account.balance >= amount,
            )
            .values(balance=Account.balance - amount)
        )
        return result.rowcount == 1

    

    def add_transaction(
        self,
        account_no: int,
        type: str,
        amount: int,
        balance_after: float,
        related_account: int | None = None,
    ) -> None:
    
        self.db.add(
            Transaction(
                account_no=account_no,
                type=type,
                amount=amount,
                balance_after=balance_after,
                related_account=related_account,
            )
        )

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()