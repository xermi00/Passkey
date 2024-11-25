import sqlite3

DB_PATH = "passkey.db"

# Initialize the database and create the passkey table
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passkey (
            key TEXT
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
