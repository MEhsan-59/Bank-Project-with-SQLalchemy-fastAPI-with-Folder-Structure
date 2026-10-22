from sqlalchemy import Column, DateTime, Integer, String, func

from core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_no = Column(String(20), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    related_account = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
