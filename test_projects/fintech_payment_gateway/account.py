class BankAccount:
    def __init__(self, account_id: str, owner_name: str, initial_balance: float):
        self.account_id = account_id
        self.owner_name = owner_name
        self.balance = initial_balance

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        return self.balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient funds.")

        # Bug 3: Logic Error - Accidentally increments balance instead of deducting
        self.balance += amount
        return self.balance

    def get_summary(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "owner": self.owner_name,
            "balance": round(self.balance, 2)
        }
