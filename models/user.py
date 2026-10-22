from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(30), unique=True, index=True, nullable=False)
    user_name = Column(String(50), nullable=False)
    account_no = Column(String(20), unique=True, index=True, nullable=False)
    balance = Column(Integer, nullable=False, default=0)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    email = Column(String(100), unique=True, index=True, nullable=True)
    freeze = Column(Boolean, nullable=False, default=False)
    