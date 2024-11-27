from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
from threading import Thread

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing
logging.basicConfig(level=logging.INFO)

# Database path
DB_PATH = "passkey.db"

# Data stores for tracking users
PENDING_USERS = {}
APPROVED_USERS = {}
DENIED_USERS = {}
USER_STATUSES = {}  # Tracks user status ("unbanned", "banned")
BANNED_USERS = {}

# Initialize the database if it doesn't exist
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Create passkey table if it doesn't exist
        cursor.execute("""CREATE TABLE IF NOT EXISTS passkey (key TEXT)""")
        # Create user status table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_status (
                username TEXT PRIMARY KEY,
                status TEXT
            )
        """)
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

# Utility to update user status in memory and the database
def update_user_status(username, status):
    USER_STATUSES[username] = status
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_status (username, status)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET status = excluded.status
        """, (username, status))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error while updating status: {e}")
    finally:
        if conn:
            conn.close()
    logging.info(f"Status for {username} updated to {status}.")

# Load user statuses from the database
def load_user_statuses():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, status FROM user_status")
        rows = cursor.fetchall()
        for username, status in rows:
            USER_STATUSES[username] = status
    except sqlite3.Error as e:
        logging.error(f"Database error while loading statuses: {e}")
    finally:
        if conn:
            conn.close()

# Root route
@app.route('/')
def home():
    return jsonify({"message": "Service is running!"})

# Unban detection route
@app.route('/unban-detection', methods=['GET'])
def unban_detection():
    username = request.args.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    status = USER_STATUSES.get(username, None)
    if status == "unbanned":
        return jsonify({"status": "unbanned", "username": username}), 200
    elif status == "banned":
        return jsonify({"status": "banned", "username": username}), 200
    else:
        return jsonify({"status": "unknown", "message": "Username not found"}), 404

# Existing routes for ban, unban, register, etc.

# Ban a user
@app.route('/ban', methods=['POST'])
def ban_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if username in APPROVED_USERS or username in USER_STATUSES:
        BANNED_USERS[username] = True
        update_user_status(username, "banned")
        return jsonify({"status": "success", "message": f"Username {username} banned"}), 200
    else:
        return jsonify({"status": "failure", "message": f"Username {username} not found in approved list"}), 404

# Unban a user
@app.route('/unban', methods=['POST'])
def unban_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if username in BANNED_USERS:
        BANNED_USERS.pop(username, None)
        update_user_status(username, "unbanned")
        return jsonify({"status": "success", "message": f"Username {username} unbanned"}), 200
    else:
        return jsonify({"status": "failure", "message": f"Username {username} not found in banned list"}), 404

# Flask application startup
if __name__ == "__main__":
    init_db()
    load_user_statuses()
    Thread(target=handle_command, daemon=True).start()
    app.run(debug=False, port=5000)
