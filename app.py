from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
from threading import Thread
import time

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
        cursor.execute("""CREATE TABLE IF NOT EXISTS passkey (key TEXT)""")
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

# Utility to update user status
def update_user_status(username, status):
    USER_STATUSES[username] = status
    logging.info(f"Status for {username} updated to {status}.")

# Root route
@app.route('/')
def home():
    return jsonify({"message": "Service is running!"})

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

# Status Check (updated to include ban/unban logic)
@app.route('/status', methods=['GET'])
def status():
    username = request.args.get('username')

    if username in BANNED_USERS:
        return jsonify({"status": "banned", "username": username}), 200
    elif username in APPROVED_USERS:
        return jsonify({"status": "approved", "username": username}), 200
    elif username in PENDING_USERS:
        return jsonify({"status": "pending"}), 200
    elif username in DENIED_USERS:
        return jsonify({"status": "denied", "message": DENIED_USERS[username]}), 200
    else:
        return jsonify({"status": "not_found", "message": "Username not found"}), 404

# Other Routes (Register, Approve, Deny, etc.)
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if " " in username or len(username) > 15:
        return jsonify({"status": "failure", "message": "Invalid username format"}), 400

    logging.info(f"Username {username} has attempted to access the project.")
    PENDING_USERS[username] = "Pending"
    update_user_status(username, "unbanned")
    return jsonify({"status": "success", "message": "Username submitted for approval"}), 200

@app.route('/approve', methods=['POST'])
def approve_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if username in PENDING_USERS:
        PENDING_USERS.pop(username, None)
        APPROVED_USERS[username] = True
        update_user_status(username, "unbanned")
        logging.info(f"Username {username} has been approved.")
        return jsonify({"status": "success", "message": f"Username {username} approved"}), 200
    else:
        return jsonify({"status": "failure", "message": f"Username {username} not found in pending list"}), 404

# Administrative command handler
def handle_command():
    while True:
        command = input("Enter command (/accept [username], /deny [username] [reason], /ban [username], /unban [username]): ").strip()
        if command.startswith("/accept"):
            _, username = command.split(" ", 1)
            if username in PENDING_USERS:
                PENDING_USERS.pop(username, None)
                APPROVED_USERS[username] = True
                update_user_status(username, "unbanned")
                logging.info(f"Username {username} has been approved.")
            else:
                print(f"Username {username} is not pending approval.")
        elif command.startswith("/deny"):
            parts = command.split(" ", 2)
            if len(parts) < 3:
                print("Invalid /deny command. Usage: /deny [username] [reason]")
                continue
            _, username, reason = parts
            if username in PENDING_USERS:
                PENDING_USERS.pop(username, None)
                DENIED_USERS[username] = reason
                update_user_status(username, "denied")
                logging.info(f"Username {username} has been denied: {reason}")
            else:
                print(f"Username {username} is not pending approval.")
        elif command.startswith("/ban"):
            _, username = command.split(" ", 1)
            if username in APPROVED_USERS or username in USER_STATUSES:
                BANNED_USERS[username] = True
                update_user_status(username, "banned")
                logging.info(f"Username {username} has been banned.")
            else:
                print(f"Username {username} is not in approved list.")
        elif command.startswith("/unban"):
            _, username = command.split(" ", 1)
            if username in BANNED_USERS:
                BANNED_USERS.pop(username, None)
                update_user_status(username, "unbanned")
                logging.info(f"Username {username} has been unbanned.")
            else:
                print(f"Username {username} is not in banned list.")

if __name__ == "__main__":
    init_db()
    Thread(target=handle_command, daemon=True).start()
    app.run(debug=True, host="0.0.0.0", port=5000)
