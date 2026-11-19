import os
import re

# 1. SECURITY VULNERABILITY (Aegis should flag)
STRIPE_SECRET_KEY = "MOCK_SECRET_KEY_EXPOSED_9482938472938472"

def query_customer_orders(customer_id):
    # 2. SQL INJECTION (Aegis should flag)
    query = "SELECT * FROM orders WHERE customer_id = " + str(customer_id)
    return query

def calculate_discount(price, discount_rate=0.1, audit_trail=[]):
    # 3. MUTABLE DEFAULT ARGUMENT (Dr. Patch should flag)
    audit_trail.append(price)
    discounted = price * (1 - discount_rate)
    return discounted

def compute_order_statistics(customers):
    # 4. O(N^3) TRIPLE NESTED LOOP (Nova should flag for CPU/Complexity)
    total_revenue = 0
    for customer in customers:
        for order in customer.get("orders", []):
            for item in order.get("items", []):
                total_revenue += item.get("price", 0)
    return total_revenue

def process_checkout(cart_items, user_id):
    # 5. UNGUARDED DIVISION BY ZERO (Dr. Patch should flag)
    total_amount = sum(item["price"] for item in cart_items)
    average_item_price = total_amount / len(cart_items)
    
    # 6. UNCLOSED FILE HANDLE (Nova should flag for Resource Leak)
    log_file = open("checkout_audit.log", "a")
    log_file.write(f"User {user_id} checkout: {total_amount}\n")
    
    # 7. DEAD UNREACHABLE CODE (Dr. Patch should flag)
    return average_item_price
    print("Checkout complete for user: " + str(user_id))

if __name__ == "__main__":
    print("E-Commerce Order Processing Engine Online")
