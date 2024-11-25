import sqlite3
import logging

DB_PATH = "passkey.db"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create the passkey table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT NOT NULL
            )
        """)
        logging.info("Passkey table initialized.")

        # Insert default passkey if the table is empty
        cursor.execute("SELECT COUNT(*) FROM passkey")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
            logging.info("Inserted default passkey.")

        # Create the registrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        """)
        logging.info("Registrations table initialized.")

        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    logging.info("Database setup complete.")
