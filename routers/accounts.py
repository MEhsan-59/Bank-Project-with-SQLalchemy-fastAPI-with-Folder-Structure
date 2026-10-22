from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from repositories.admin_repository import AdminRepository
from repositories.account_repository import AccountRepository
from schemas.accounts import (
    AccountCreate,
    AccountCreated,
    AccountLogin,
    ChangePasswordRequest,
    ChangePasswordResponse,
    AccessToken,
)
from services.admin_service import AdminService
from services.account_service import AccountService
from utils.dependencies import get_current_account
from models import Account

router = APIRouter()


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(
        AccountRepository(db),
        AdminRepository(settings.ADMIN_FILE),
    )


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(
        AdminRepository(settings.ADMIN_FILE),
        AccountRepository(db),
    )


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
    admin_service: AdminService = Depends(get_admin_service),
) -> AccessToken:
    admin_token = admin_service.login(data.user_id, data.password)
    if admin_token is not None:
        return AccessToken(access_token=admin_token, token_type="bearer")

    token = service.login(data.user_id, data.password)
    if token is None:
        raise HTTPException(
            status_code=401, detail="Invalid user_id or password"
        )
    return AccessToken(access_token=token, token_type="bearer")


@router.post("/change_password", response_model=ChangePasswordResponse)
def change_password(
    data: ChangePasswordRequest,
    account: Account = Depends(get_current_account),
    service: AccountService = Depends(get_account_service),
) -> ChangePasswordResponse:
    error = service.change_password(
        account,
        data.old_password,
        data.new_password,
        data.confirm_password,
    )
    if error is not None:
        raise HTTPException(status_code=400, detail=error)
    return ChangePasswordResponse(
        success=True,
        message="Password successfully changed.",
    )
