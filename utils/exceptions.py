# utils/exceptions.py
class BankError(Exception):
    status_code = 400
    message = "Bad request."

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)


class InsufficientBalance(BankError):
    status_code = 400
    message = "Insufficient balance."

class ReceiverNotFound(BankError):
    status_code = 404
    message = "Receiver account not found."


class AccountNotFound(BankError):
    status_code = 404
    message = "Account not found."


class AccountFrozen(BankError):
    status_code = 403
    message = "Your account is frozen. Please contact the admin."


class SelfTransfer(BankError):
    status_code = 400
    message = "You cannot send money to your own account."


class TransactionNotFound(BankError):
    status_code = 404
    message = "Transaction not found or already used."


class ForbiddenAction(BankError):
    status_code = 403
    message = "This action is not allowed."

class TransferIdNotFound(BankError):
    status_code = 404
    message = "Transfer ID not found."

class InvalidUserIdOrPassword(BankError):
    status_code = 401
    message = "Invalid user_id or password."