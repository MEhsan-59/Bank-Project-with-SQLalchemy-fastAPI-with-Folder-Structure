from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from models import Account, PendingTransfer, Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_pending_transfer(
        self,
        sender_user_id: str,
        receiver_account_no: str,
        amount: int,
    ) -> PendingTransfer:
        transfer = PendingTransfer(
            transfer_id=str(uuid4()),
            sender_user_id=sender_user_id,
            receiver_account_no=receiver_account_no,
            amount=amount,
        )
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        return transfer

    def get_pending_transfer(self, transfer_id: str) -> PendingTransfer | None:
        return (
            self.db.query(PendingTransfer)
            .filter(PendingTransfer.transfer_id == transfer_id)
            .first()
        )

    def deposit(self, user_id: str, amount: int) -> int | None:
        result = self.db.execute(
            update(Account)
            .where(Account.user_id == user_id)
            .values(balance=Account.balance + amount)
        )
        if result.rowcount != 1:
            self.db.rollback()
            return None
        account = (
            self.db.query(Account)
            .filter(Account.user_id == user_id)
            .one()
        )
        self.db.add(
            Transaction(
                account_no=account.account_no,
                type="deposit",
                amount=amount,
                balance_after=account.balance,
            )
        )
        self.db.commit()
        return account.balance

    def confirm_transfer(
        self, sender_user_id: str, transfer_id: str
    ) -> str:
        transfer = self.get_pending_transfer(transfer_id)
        if transfer is None:
            return "not_found"
        if transfer.sender_user_id != sender_user_id:
            return "forbidden"

        receiver = (
            self.db.query(Account)
            .filter(Account.account_no == transfer.receiver_account_no)
            .first()
        )
        if receiver is None:
            return "receiver_not_found"
        sender_account_no = self.db.scalar(
            select(Account.account_no).where(Account.user_id == sender_user_id)
        )
        if sender_account_no is None:
            return "not_found"

        amount = transfer.amount
        removed = self.db.execute(
            delete(PendingTransfer).where(
                PendingTransfer.transfer_id == transfer_id,
                PendingTransfer.sender_user_id == sender_user_id,
            )
        )
        if removed.rowcount != 1:
            self.db.rollback()
            return "not_found"

        debited = self.db.execute(
            update(Account)
            .where(
                Account.user_id == sender_user_id,
                Account.freeze.is_(False),
                Account.balance >= amount,
            )
            .values(balance=Account.balance - amount)
        )
        if debited.rowcount != 1:
            sender = (
                self.db.query(Account)
                .filter(Account.user_id == sender_user_id)
                .first()
            )
            self.db.rollback()
            if sender is not None and sender.freeze:
                return "account_frozen"
            return "insufficient_balance"

        credited = self.db.execute(
            update(Account)
            .where(Account.account_no == transfer.receiver_account_no)
            .values(balance=Account.balance + amount)
        )
        if credited.rowcount != 1:
            self.db.rollback()
            return "receiver_not_found"

        sender_balance = self.db.scalar(
            select(Account.balance).where(Account.user_id == sender_user_id)
        )
        receiver_balance = self.db.scalar(
            select(Account.balance).where(
                Account.account_no == transfer.receiver_account_no
            )
        )
        self.db.add_all(
            [
                Transaction(
                    account_no=sender_account_no,
                    type="transfer_out",
                    amount=amount,
                    balance_after=sender_balance,
                    related_account=transfer.receiver_account_no,
                ),
                Transaction(
                    account_no=transfer.receiver_account_no,
                    type="transfer_in",
                    amount=amount,
                    balance_after=receiver_balance,
                    related_account=sender_account_no,
                ),
            ]
        )
        self.db.commit()
        return "success"
