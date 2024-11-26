from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
from threading import Thread
import time

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Database path
DB_PATH = "passkey.db"

# Data stores for tracking users
PENDING_USERS = {}
APPROVED_USERS = {}
DENIED_USERS = {}
BANNED_USERS = {}

# Initialize the database if it doesn't exist
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT
            )
        """)
        # Insert default passkey if the table is empty
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

    if username in APPROVED_USERS:
        APPROVED_USERS.pop(username)
        BANNED_USERS[username] = True
        logging.info(f"Username {username} has been banned.")
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
        BANNED_USERS.pop(username)
        APPROVED_USERS[username] = True
        logging.info(f"Username {username} has been unbanned.")
        return jsonify({"status": "success", "message": f"Username {username} unbanned"}), 200
    else:
        return jsonify({"status": "failure", "message": f"Username {username} not found in banned list"}), 404

# Check user status
@app.route('/status', methods=['GET'])
def status():
    username = request.args.get('username')

    if username in BANNED_USERS:
        return jsonify({"status": "banned", "message": "User is banned"}), 200
    elif username in APPROVED_USERS:
        return jsonify({"status": "approved", "username": username}), 200
    elif username in PENDING_USERS:
        return jsonify({"status": "pending"}), 200
    elif username in DENIED_USERS:
        return jsonify({"status": "denied", "message": DENIED_USERS[username]}), 200
    else:
        return jsonify({"status": "not_found", "message": "Username not found"}), 404

# Administrative command handler
def handle_command():
    while True:
        command = input("Enter command (/accept [username], /deny [username] [reason], /ban [username], /unban [username]): ").strip()
        parts = command.split(" ", 2)
        if len(parts) < 2:
            print("Invalid command.")
            continue

        action = parts[0]
        username = parts[1]

        if action == "/accept" and username in PENDING_USERS:
            PENDING_USERS.pop(username)
            APPROVED_USERS[username] = True
            logging.info(f"Username {username} has been approved.")
        elif action == "/deny" and len(parts) == 3 and username in PENDING_USERS:
            reason = parts[2]
            PENDING_USERS.pop(username)
            DENIED_USERS[username] = reason
            logging.info(f"Username {username} has been denied for reason: {reason}")
        elif action == "/ban" and username in APPROVED_USERS:
            APPROVED_USERS.pop(username)
            BANNED_USERS[username] = True
            logging.info(f"Username {username} has been banned.")
        elif action == "/unban" and username in BANNED_USERS:
            BANNED_USERS.pop(username)
            APPROVED_USERS[username] = True
            logging.info(f"Username {username} has been unbanned.")
        else:
            print(f"Invalid action or username: {username} not found in the appropriate list.")

if __name__ == "__main__":
    # Initialize the database
    init_db()
    # Start the command handler in a separate thread
    Thread(target=handle_command, daemon=True).start()
    app.run(debug=True, host="0.0.0.0", port=5000)
