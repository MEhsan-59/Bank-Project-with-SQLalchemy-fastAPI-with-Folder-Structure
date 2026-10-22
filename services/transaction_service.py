from models import Account, PendingTransfer
from repositories.transaction_repository import TransactionRepository
from repositories.account_repository import AccountRepository


class TransactionService:
    def __init__(
        self,
        transactions: TransactionRepository,
        accounts: AccountRepository,
    ):
        self.transactions = transactions
        self.accounts = accounts

    def deposit(self, account: Account, amount: int) -> int | None:
        return self.transactions.deposit(account.user_id, amount)

    def preview_transfer(
        self, sender: Account, receiver_account_no: str, amount: int
    ) -> tuple[PendingTransfer | None, str | None]:
        if sender.freeze:
            return None, "account_frozen"
        if sender.account_no == receiver_account_no:
            return None, "self_transfer"

        receiver = self.accounts.get_by_account_no(receiver_account_no)
        if receiver is None:
            return None, "receiver_not_found"

        if sender.balance < amount:
            return None, "insufficient_balance"

        transfer = self.transactions.create_pending_transfer(
            sender.user_id, receiver.account_no, amount
        )
        return transfer, None

    def confirm_transfer(self, sender: Account, transfer_id: str) -> str:
        return self.transactions.confirm_transfer(sender.user_id, transfer_id)
