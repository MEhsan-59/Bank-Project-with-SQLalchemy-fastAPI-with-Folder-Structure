from logging import getLogger
from models import Account, PendingTransfer
from repositories.account_repository import AccountRepository
from repositories.transaction_repository import TransactionRepository
from utils.exceptions import (AccountFrozen, InsufficientBalance, ReceiverNotFound, SelfTransfer, TransactionNotFound, ForbiddenAction)

class TransactionService:
    def __init__(self, transactions: TransactionRepository, accounts: AccountRepository,):
        self.transactions = transactions
        self.accounts = accounts
        self.logger = getLogger(__name__)

    def deposit(self, account: Account, amount: int) -> int | None:
        if not self.accounts.credit(account.account_no, amount):
            self.transactions.rollback()
            self.logger.warning(
                "Deposit could not be completed for account %s.",
                account.account_no,
            )
            return None

        balance = self.accounts.get_balance(account.account_no)
        self.transactions.add_transaction(
            account.account_no, "deposit", amount, balance
        )
        self.transactions.commit()
        self.logger.info("Deposit completed for account %s.", account.account_no)
        return balance

    def preview_transfer(self, sender: Account, receiver_account_no: str, amount: int):
        if sender.freeze:
            self.logger.warning("Frozen account %s attempted to preview a transfer.",sender.account_no,)
            raise AccountFrozen()
        if sender.account_no == receiver_account_no:
            self.logger.warning(
                "Account %s attempted to transfer money to itself.",
                sender.account_no,
            )
            raise SelfTransfer()
        receiver = self.accounts.get_by_account_no(receiver_account_no)
        if receiver is None:
            self.logger.warning(
                "Transfer preview for account %s used an unknown receiver.",
                sender.account_no,
            )
            raise ReceiverNotFound()
        if sender.balance < amount:
            self.logger.warning(
                "Account %s attempted a transfer with insufficient balance.",
                sender.account_no,
            )
            raise InsufficientBalance()
        pending =  self.transactions.add_pending_transfer(sender.user_id, receiver.account_no, amount)
        self.logger.info("Transfer preview created for account %s.", sender.account_no)
        return pending

    def confirm_transfer(self, sender: Account, transfer_id: str) -> str:
        transfer = self.transactions.get_pending_transfer(transfer_id)
        if transfer is None:
            self.logger.warning(
                "Account %s attempted to confirm an unknown transfer.",
                sender.account_no,
            )
            raise TransactionNotFound()
        if transfer.sender_user_id != sender.user_id:
            self.logger.warning(
                "User %s attempted to confirm transfer %s not belonging to them.",
                sender.user_id,
                transfer_id,
            )
            raise ForbiddenAction("You are not authorized to confirm this transfer.")

        if self.accounts.get_by_account_no(transfer.receiver_account_no) is None:
            self.logger.warning(
                "Transfer %s could not be confirmed because its receiver no longer exists.",
                transfer_id,
            )
            raise ReceiverNotFound()
        amount = transfer.amount
        receiver_no = transfer.receiver_account_no
        if not self.transactions.delete_pending_transfer(transfer):
            self.transactions.rollback()
            self.logger.warning("Transfer %s was already used or could not be found.", transfer_id)
            raise TransactionNotFound()
        if not self.transactions.debit(sender.user_id, amount):
            self.transactions.rollback()
            if sender.freeze:
                self.logger.warning(
                    "Frozen account %s attempted to confirm transfer %s.",
                    sender.account_no,
                    transfer_id,
                )
                raise AccountFrozen()
            self.logger.warning(
                "Account %s had insufficient balance to confirm transfer %s.",
                sender.account_no,
                transfer_id,
            )
            raise InsufficientBalance()
        if not self.accounts.credit(receiver_no, amount):
            self.transactions.rollback()
            self.logger.error(
                "Transfer %s could not be credited to its receiver.",
                transfer_id,
            )
            raise ReceiverNotFound()

        sender_balance = self.accounts.get_balance(sender.account_no)
        receiver_balance = self.accounts.get_balance(receiver_no)
        self.transactions.add_transaction(
            sender.account_no, "transfer_out", amount, sender_balance, receiver_no
        )
        self.transactions.add_transaction(
            receiver_no, "transfer_in", amount, receiver_balance, sender.account_no)

        self.transactions.commit()
        self.logger.info("Transfer %s confirmed by account %s.", transfer_id, sender.account_no)
        return "success"
