from models import Account
from repositories.account_repository import AccountRepository
from utils.security import create_access_token, hash_password, verify_password


class AccountService:
    def __init__(self, repository: AccountRepository):
        self.repository = repository

    def create_account(
        self, user_id: str, user_name: str, password: str
    ) -> Account | None:
        if self.repository.get_by_user_id(user_id) is not None:
            return None
        return self.repository.create(user_id, user_name, password)

    def login(self, user_id: str, password: str) -> str | None:
        account = self.repository.authenticate(user_id, password)
        if account is None:
            return None
        return create_access_token(account.user_id)

    def change_password(
        self,
        account: Account,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> str | None:
        if not verify_password(old_password, account.password):
            return "Old password does not match."
        if new_password != confirm_password:
            return "New password and confirm password do not match."

        self.repository.update_password(account, hash_password(new_password))
        return None
