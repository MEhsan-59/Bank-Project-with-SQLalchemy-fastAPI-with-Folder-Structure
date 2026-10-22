from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from models import Account
from repositories.account_repository import AccountRepository
from utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")

    payload = decode_access_token(credentials.credentials)
    if payload is None or payload.get("role") != "user":
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    account = AccountRepository(db).get_by_user_id(user_id)
    if account is None:
        raise HTTPException(status_code=401, detail="User not found.")
    return account
