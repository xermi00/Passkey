import sqlite3
import logging
import os

# Database file path
DB_PATH = "passkey.db"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def init_db():
    """Initializes the database and ensures required tables exist."""
    if not os.path.exists(DB_PATH):
        logging.info(f"Database file {DB_PATH} not found. It will be created.")
    
    conn = None
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create the passkey table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT NOT NULL
            )
        """)
        logging.info("Checked or created 'passkey' table.")

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
        logging.info("Checked or created 'registrations' table.")

        # Commit the changes
        conn.commit()
        logging.info("Database initialized successfully.")
    
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        # Ensure the cursor is closed
        if conn:
            conn.close()
            logging.info("Database connection closed.")


if __name__ == "__main__":
    init_db()
    logging.info("Database setup complete.")
