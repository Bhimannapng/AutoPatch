def calculate_discount(price, rate=0.1):
    if price < 0 or rate < 0:
        return 0.0
    discount = price * rate
    return discount
