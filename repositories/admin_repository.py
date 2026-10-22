import json
from pathlib import Path
from typing import Any

from utils.security import verify_password


class AdminRepository:
    def __init__(self, file_name: str | Path):
        self.file_name = Path(file_name)

    def load_admins(self) -> list[dict[str, Any]]:
        with self.file_name.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("Admin configuration must be a JSON object.")
        admins = data.get("admins")
        if not isinstance(admins, list):
            raise ValueError("Admin configuration must contain an admins list.")
        if not all(isinstance(admin, dict) for admin in admins):
            raise ValueError("Each admin configuration entry must be an object.")
        return admins

    def get_admin_by_username(self, username: str) -> dict[str, Any] | None:
        return next(
            (
                admin
                for admin in self.load_admins()
                if admin.get("username") == username
            ),
            None,
        )

    def username_exists(self, username: str) -> bool:
        return self.get_admin_by_username(username) is not None

    def authenticate(
        self, username: str, password: str
    ) -> dict[str, Any] | None:
        admin = self.get_admin_by_username(username)
        if admin is None:
            return None
        hashed_password = admin.get("password")
        if not isinstance(hashed_password, str):
            return None
        if not verify_password(password, hashed_password):
            return None
        return admin
