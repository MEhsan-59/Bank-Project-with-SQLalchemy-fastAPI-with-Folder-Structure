from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models import Account
from repositories.statement_repository import StatementRepository
from schemas.statements import StatementResponse
from services.statement_service import StatementService
from utils.dependencies import get_current_account

router = APIRouter()


def get_statement_service(
    db: Session = Depends(get_db),
) -> StatementService:
    return StatementService(StatementRepository(db))


@router.get("/statements", response_model=StatementResponse)
def get_statements(
    account: Account = Depends(get_current_account),
    service: StatementService = Depends(get_statement_service),
) -> StatementResponse:
    return StatementResponse(
        transactions=service.get_history(account.account_no)
    )


@router.get("/mini_statements", response_model=StatementResponse)
def get_mini_statements(
    account: Account = Depends(get_current_account),
    service: StatementService = Depends(get_statement_service),
) -> StatementResponse:
    return StatementResponse(
        transactions=service.get_mini_history(account.account_no)
    )
