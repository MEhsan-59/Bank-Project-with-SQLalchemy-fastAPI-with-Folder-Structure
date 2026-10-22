from models import Transaction
from repositories.statement_repository import StatementRepository


class StatementService:
    def __init__(self, repository: StatementRepository):
        self.repository = repository

    def get_history(self, account_no: str) -> list[Transaction]:
        return self.repository.get_history(account_no)

    def get_mini_history(self, account_no: str) -> list[Transaction]:
        return self.repository.get_top_5_history(account_no)
