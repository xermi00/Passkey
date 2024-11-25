import sqlite3

DB_PATH = "passkey.db"

# Initialize the database and create necessary tables
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the passkey table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passkey (
            key TEXT
        )
    """)

    # Create the users table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT UNIQUE,
            status TEXT,
            reason TEXT
        )
    """)

    # Insert an initial passkey if the table is empty
    cursor.execute("SELECT COUNT(*) FROM passkey")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
        print("Inserted default passkey.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
