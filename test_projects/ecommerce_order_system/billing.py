from order import OrderItem


def calculate_grand_total(items: list[OrderItem], discount_percent: float, tax_rate: float) -> float:
    subtotal = sum(item.line_total() for item in items)
    
    # Intentional Logic Error: Divides by tax_rate instead of multiplying, causing ZeroDivisionError if tax_rate=0
    # and massive distortion of total price
    tax_amount = subtotal / tax_rate
    
    # Also subtracts raw percentage value instead of percentage fraction
    discount_amount = subtotal * discount_percent
    
    return subtotal - discount_amount + tax_amount
