from repositories.account_repository import AccountRepository
from repositories.admin_repository import AdminRepository
from utils.security import create_access_token


class AdminService:
    def __init__(self,admin_repository: AdminRepository,account_repository: AccountRepository | None = None,):
        self.admin_repository = admin_repository
        self.account_repository = account_repository

    def login(self, username: str, password: str) -> str | None:
        if not username.strip() or not password.strip():
            return None
        admin = self.admin_repository.authenticate(username, password)
        if admin is None:
            return None
        permissions = admin.get("permissions", [])
        if not isinstance(permissions, list) or not all(isinstance(permission, str) for permission in permissions):
            raise ValueError(f"Admin permissions must be a list of strings: {username}")
        return create_access_token(
            username,
            role="admin",
            extra_claims={"permissions": permissions},
        )

    def freeze_account(self, account_no: str) -> bool:
        if self.account_repository is None:
            raise RuntimeError("Account repository is required to freeze accounts.")
        return self.account_repository.freeze_account(account_no)

    def unfreeze_account(self, account_no: str) -> bool:
        if self.account_repository is None:
            raise RuntimeError("Account repository is required to unfreeze accounts.")
        return self.account_repository.unfreeze_account(account_no)
