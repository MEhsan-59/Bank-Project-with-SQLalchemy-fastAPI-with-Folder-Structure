from sqlalchemy.orm import Session
from models import Transaction

class StatementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_history(
        self, account_no: str, limit: int | None = None
    ) -> list[Transaction]:
        query = (
            self.db.query(Transaction)
            .filter(Transaction.account_no == account_no)
            .order_by(Transaction.id.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_top_5_history(self, account_no: str) -> list[Transaction]:
        return self.get_history(account_no, limit=5)
