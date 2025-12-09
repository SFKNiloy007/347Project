import bcrypt
from database import DatabaseManager

# Generate correct password hash
password = "password123"
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

print(f"Generated hash: {password_hash}")

# Update database
db = DatabaseManager()

for username in ['artisan1', 'buyer1', 'admin1']:
    query = "UPDATE users SET password_hash = %s WHERE username = %s"
    rows = db.execute_update(query, (password_hash, username))
    print(f"Updated {username}: {rows} row(s)")

print("\nVerifying...")
for username in ['artisan1', 'buyer1', 'admin1']:
    query = "SELECT password_hash FROM users WHERE username = %s"
    result = db.execute_query(query, (username,))
    if result:
        stored_hash = result[0]['password_hash']
        is_valid = bcrypt.checkpw(password.encode(), stored_hash.encode())
        print(f"{username}: Valid={is_valid}")
