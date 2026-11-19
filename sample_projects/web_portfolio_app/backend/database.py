import os

# 1. SECURITY VULNERABILITY (Aegis): Hardcoded Secret
DATABASE_API_KEY = "MOCK_DB_SECRET_KEY_EXPOSED_98374928"

def get_db_connection():
    print("Connecting to database using API key:", DATABASE_API_KEY)
    return {"status": "connected"}

def find_user_by_email(email):
    # 2. SECURITY VULNERABILITY (Aegis): Raw SQL Injection
    query = "SELECT * FROM users WHERE email = '" + email + "'"
    return query
