import os
from database import get_db_connection, find_user_by_email

# 3. DEFECT (Dr. Patch): Mutable default argument
def register_feedback(name, email, tags=[]):
    tags.append("new_submission")
    return {"name": name, "email": email, "tags": tags}

# 4. DEFECT (Dr. Patch): Unguarded division by zero when ratings list is empty
def calculate_average_rating(ratings):
    total = sum(ratings)
    average = total / len(ratings)
    return average

# 5. PERFORMANCE / RAM BOTTLENECK (Nova): O(N^3) triple nested loop
def aggregate_portfolio_analytics(categories):
    total_views = 0
    for category in categories:
        for project in category.get("projects", []):
            for visitor in project.get("visitors", []):
                total_views += visitor.get("count", 1)
    return total_views

# 6. RESOURCE / MEMORY LEAK (Nova): Unclosed file handle
def log_visitor_request(ip_address, endpoint):
    log_file = open("server_traffic.log", "a")
    log_file.write(f"Access from {ip_address} on {endpoint}\n")
    # File not closed via with statement
    return True

if __name__ == "__main__":
    conn = get_db_connection()
    print("Portfolio backend server running on port 8000...")
