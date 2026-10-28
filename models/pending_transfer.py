from sqlalchemy import BigInteger, Column, DateTime, Integer, String, func
from core.database import Base

pending_transfer_base = Base

class PendingTransfer(pending_transfer_base):
    __tablename__ = "Pending_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(String(36), unique=True, index=True, nullable=False)
    sender_user_id = Column(String(30), nullable=False, index=True)
    receiver_account_no = Column(String(20), nullable=False)
    amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
