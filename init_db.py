import sqlite3
import logging

DB_PATH = "passkey.db"  # Path to your SQLite database

def init_db():
    try:
        # This will create the database file if it doesn't exist
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create passkey table if it doesn't exist
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT
            )
        """)

        # Insert a default passkey if no passkey exists
        cursor.execute("SELECT COUNT(*) FROM passkey")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
            logging.info("Inserted default passkey.")

        # Create users table if it doesn't exist
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS users (
                username TEXT UNIQUE,
                status TEXT,
                reason TEXT
            )
        """)

        conn.commit()
        logging.info("Database initialized successfully.")

    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    logging.info("Database created or already exists.")
