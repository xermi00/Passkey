from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)
DB_PATH = "passkey.db"

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Create passkey table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT
            )
        """)
        # Create registrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                reason TEXT DEFAULT NULL
            )
        """)
        # Insert default passkey if needed
        cursor.execute("SELECT COUNT(*) FROM passkey")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
            logging.info("Inserted default passkey.")
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "Username is required"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO registrations (username) VALUES (?)", (username,))
        conn.commit()
        logging.info(f"Registration attempted for username: {username}")
        return jsonify({"status": "success", "message": "Registration requested"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "failure", "message": "Username already exists"}), 409
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/update-registration', methods=['POST'])
def update_registration():
    username = request.form.get('username')
    status = request.form.get('status')
    reason = request.form.get('reason')

    if not username or not status:
        return jsonify({"status": "failure", "message": "Username and status are required"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE registrations
            SET status = ?, reason = ?
            WHERE username = ?
        """, (status, reason, username))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "Username not found"}), 404

        message = "Registration updated successfully"
        logging.info(f"{username} status updated to {status}. Reason: {reason if reason else 'None'}")
        return jsonify({"status": "success", "message": message}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
