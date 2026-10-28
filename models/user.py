from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, func, Float, Sequence
from core.database import Base


account_number_seq = Sequence("account_number_seq", start=1000000000)

user_base = Base
class Account(user_base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(30), unique=True, index=True, nullable=False)
    user_name = Column(String(50), nullable=False)
    account_no = Column(BigInteger, account_number_seq, unique=True, nullable=False)
    balance = Column(Float, nullable=False, default=0)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    email = Column(String(100), unique=True, index=True, nullable=True)
    freeze = Column(Boolean, nullable=False, default=False)
    