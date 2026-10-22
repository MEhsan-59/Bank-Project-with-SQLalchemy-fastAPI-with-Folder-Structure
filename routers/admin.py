from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from repositories.account_repository import AccountRepository
from repositories.admin_repository import AdminRepository
from repositories.statement_repository import StatementRepository
from schemas.admin import AdminFreezeResponse
from schemas.statements import StatementResponse
from services.admin_service import AdminService
from services.statement_service import StatementService
from utils.admin_dependencies import require_admin_permission

router = APIRouter(prefix="/admin")


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(
        AdminRepository(settings.ADMIN_FILE),
        AccountRepository(db),
    )


def get_statement_service(
    db: Session = Depends(get_db),
) -> StatementService:
    return StatementService(StatementRepository(db))


@router.post(
    "/freeze_account/{account_no}",
    response_model=AdminFreezeResponse,
)
def freeze_account(
    account_no: str,
    _: dict = Depends(require_admin_permission("freeze_account")),
    service: AdminService = Depends(get_admin_service),
) -> AdminFreezeResponse:
    if not service.freeze_account(account_no):
        raise HTTPException(
            status_code=404,
            detail="Account not found or already frozen.",
        )
    return AdminFreezeResponse(
        success=True,
        message="Account has been frozen successfully.",
    )


@router.post(
    "/unfreeze_account/{account_no}",
    response_model=AdminFreezeResponse,
)
def unfreeze_account(
    account_no: str,
    _: dict = Depends(require_admin_permission("unfreeze_account")),
    service: AdminService = Depends(get_admin_service),
) -> AdminFreezeResponse:
    if not service.unfreeze_account(account_no):
        raise HTTPException(
            status_code=404,
            detail="Account not found or not frozen.",
        )
    return AdminFreezeResponse(
        success=True,
        message="Account has been unfrozen successfully.",
    )


@router.get(
    "/statements/{account_no}",
    response_model=StatementResponse,
)
def get_account_statement(
    account_no: str,
    _: dict = Depends(require_admin_permission("view_statements")),
    service: StatementService = Depends(get_statement_service),
    admin_service: AdminService = Depends(get_admin_service),
) -> StatementResponse:
    if admin_service.account_repository is None:
        raise RuntimeError("Account repository is not configured.")
    if admin_service.account_repository.get_by_account_no(account_no) is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    return StatementResponse(
        transactions=service.get_history(account_no)
    )
