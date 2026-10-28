from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, func
from core.database import Base
transaction_base = Base

class Transaction(transaction_base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_no = Column(BigInteger, nullable=False, index=True)
    type = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    related_account = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
