class OrderItem:
    def __init__(self, item_id: str, name: str, price: float, quantity: int):
        self.item_id = item_id
        self.name = name
        self.price = price
        self.quantity = quantity

    def line_total(self) -> float:
        return self.price * self.quantity

    # Intentional Syntax Error: Missing colon ':' at the end of the def statement
    def format_summary(self) -> str
        return f"{self.item_id}: {self.name} x{self.quantity} = ${self.line_total():.2f}"
