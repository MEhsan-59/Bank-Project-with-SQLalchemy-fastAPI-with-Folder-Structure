# services/transaction_service.py
from models import Account, PendingTransfer
from repositories.account_repository import AccountRepository
from repositories.transaction_repository import TransactionRepository
from utils.exceptions import (
    AccountFrozen, InsufficientBalance, ReceiverNotFound, SelfTransfer, TransactionNotFound, ForbiddenAction
)

class TransactionService:
    def __init__(self, transactions: TransactionRepository, accounts: AccountRepository,):
        self.transactions = transactions
        self.accounts = accounts

    def deposit(self, account: Account, amount: int) -> int | None:
        if not self.transactions.credit(account.account_no, amount):
            self.transactions.rollback()
            return None

        balance = self.transactions.get_balance(account.account_no)
        self.transactions.add_transaction(
            account.account_no, "deposit", amount, balance
        )
        self.transactions.commit()
        return balance

    def preview_transfer(self, sender: Account, receiver_account_no: str, amount: int):
        if sender.freeze:
            raise AccountFrozen()
        if sender.account_no == receiver_account_no:
            raise SelfTransfer()
        receiver = self.accounts.get_by_account_no(receiver_account_no)
        if receiver is None:
            raise ReceiverNotFound()
        if sender.balance < amount:
            raise InsufficientBalance()
        pending =  self.transactions.add_pending_transfer(sender.user_id, receiver.account_no, amount)
        return pending

    def confirm_transfer(self, sender: Account, transfer_id: str) -> str:
        transfer = self.transactions.get_pending_transfer(transfer_id)
        if transfer is None:
            raise TransactionNotFound()
        if transfer.sender_user_id != sender.user_id:
            raise ForbiddenAction("You are not authorized to confirm this transfer.")
        if self.accounts.get_by_account_no(transfer.receiver_account_no) is None:
            raise ReceiverNotFound()
        amount = transfer.amount
        receiver_no = transfer.receiver_account_no
        if not self.transactions.delete_pending_transfer(transfer):
            self.transactions.rollback()
            raise TransactionNotFound()
        if not self.transactions.debit(sender.user_id, amount):
            self.transactions.rollback()
            if sender.freeze:
                raise AccountFrozen()
            raise InsufficientBalance()
        if not self.transactions.credit(receiver_no, amount):
            self.transactions.rollback()
            raise ReceiverNotFound()

        sender_balance = self.transactions.get_balance(sender.account_no)
        receiver_balance = self.transactions.get_balance(receiver_no)
        self.transactions.add_transaction(
            sender.account_no, "transfer_out", amount, sender_balance, receiver_no
        )
        self.transactions.add_transaction(
            receiver_no, "transfer_in", amount, receiver_balance, sender.account_no)

        self.transactions.commit()
        return "success"
