from sqlalchemy import Column, DateTime, Integer, String, func

from core.database import Base


class PendingTransfer(Base):
    __tablename__ = "pending_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(String(36), unique=True, index=True, nullable=False)
    sender_user_id = Column(String(30), nullable=False, index=True)
    receiver_account_no = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
