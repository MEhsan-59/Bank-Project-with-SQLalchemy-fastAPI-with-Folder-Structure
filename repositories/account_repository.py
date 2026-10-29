from select import select
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy import update

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Account
from utils.security import hash_password, verify_password


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> Account | None:
        return (
            self.db.query(Account)
            .filter(Account.user_id == user_id)
            .first()
        )

    def get_by_account_no(self, account_no: str) -> Account | None:
        return (
            self.db.query(Account)
            .filter(Account.account_no == account_no)
            .first()
        )

    def freeze_account(self, account_no: str) -> bool:
        account = self.get_by_account_no(account_no)
        if account is None or account.freeze:
            return False
        account.freeze = True
        self.db.commit()
        return True

    def unfreeze_account(self, account_no: str) -> bool:
        account = self.get_by_account_no(account_no)
        if account is None or not account.freeze:
            return False
        account.freeze = False
        self.db.commit()
        return True

    def create(
        self, user_id: str, user_name: str, password: str
    ) -> Account:
        account = Account(
            user_id=user_id,
            user_name=user_name,
            balance=0,
            password=hash_password(password),
        )
        self.db.add(account)
        try:
            self.db.flush()
            if account.id is None:
                raise RuntimeError("Database did not assign an account ID.")
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(account)
        return account

    def authenticate(self, user_id: str, password: str) -> Account | None:
        account = self.get_by_user_id(user_id)
        if account is None or not verify_password(password, account.password):
            return None
        return account

    def update_password(self, account: Account, password_hash: str) -> None:
        account.password = password_hash
        self.db.commit()
        self.db.refresh(account)

    def credit(self, account_no: int, amount: int) -> bool:
        result = self.db.execute(
            update(Account)
            .where(Account.account_no == account_no)
            .values(balance=Account.balance + amount)
        )
        return result.rowcount == 1
    
    def get_balance(self, account_no: int) -> float | None:
        return self.db.scalar(select(Account.balance).where(Account.account_no == account_no))