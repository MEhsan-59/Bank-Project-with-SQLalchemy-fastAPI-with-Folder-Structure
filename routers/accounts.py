from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from repositories.account_repository import AccountRepository
from schemas.accounts import (
    AccountCreate,
    AccountCreated,
    AccountLogin,
    AccessToken,
)
from services.account_service import AccountService

router = APIRouter()


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(AccountRepository(db))


@router.post("/create_account", response_model=AccountCreated)
def create_account(
    data: AccountCreate,
    service: AccountService = Depends(get_account_service),
) -> AccountCreated:
    try:
        account = service.create_account(
            data.user_id, data.user_name, data.password
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Account already exists."
        ) from exc

    if account is None:
        raise HTTPException(status_code=409, detail="Account already exists.")

    return AccountCreated(
        status=True,
        message=(
            "Account Successfully created "
            f"Your account_no is {account.account_no}."
        ),
    )


@router.post("/login_account", response_model=AccessToken)
def login_account(
    data: AccountLogin,
    service: AccountService = Depends(get_account_service),
) -> AccessToken:
    token = service.login(data.user_id, data.password)
    if token is None:
        raise HTTPException(
            status_code=401, detail="Invalid user_id or password"
        )
    return AccessToken(access_token=token, token_type="bearer")
