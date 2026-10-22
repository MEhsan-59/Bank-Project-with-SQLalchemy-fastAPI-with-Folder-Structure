from uuid import uuid4

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

    def create(
        self, user_id: str, user_name: str, password: str
    ) -> Account:
        account = Account(
            user_id=user_id,
            user_name=user_name,
            account_no=f"TEMP-{uuid4().hex}",
            balance=0,
            password=hash_password(password),
        )
        self.db.add(account)
        try:
            self.db.flush()
            if account.id is None:
                raise RuntimeError("Database did not assign an account ID.")
            account.account_no = f"AC{3999 + account.id:04d}"
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
