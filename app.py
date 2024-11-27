from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
from threading import Thread
from datetime import datetime

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

# Logs of banned and unbanned actions
ACTION_LOGS = []

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
    log_action(username, status)
    logging.info(f"Status for {username} updated to {status}.")

# Utility to log actions
def log_action(username, action):
    ACTION_LOGS.append({"username": username, "action": action, "timestamp": datetime.utcnow().isoformat()})
    logging.info(f"Action logged: {username} -> {action}")

# Utility to get recent logs for a username
def get_recent_logs(username):
    return [log for log in ACTION_LOGS if log["username"] == username]

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

# Kick a user
@app.route('/kick', methods=['POST'])
def kick_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if username in APPROVED_USERS:
        logging.info(f"Username {username} has been kicked.")
        return jsonify({"status": "success", "message": f"Username {username} kicked"}), 200
    else:
        return jsonify({"status": "failure", "message": f"Username {username} not found in approved list"}), 404

# Passkey verification
@app.route('/verify', methods=['POST'])
def verify_passkey():
    user_passkey = request.form.get('passkey')

    if not user_passkey:
        return jsonify({"status": "failure", "message": "No passkey provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT key FROM passkey")
        stored_passkey = cursor.fetchone()

        if stored_passkey is None:
            return jsonify({"status": "failure", "message": "No passkey stored"}), 404

        if user_passkey == stored_passkey[0]:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failure", "message": "Incorrect passkey"}), 401
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

# Check user status
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

# Fetch logs for a specific user (used by Unity for unban check)
@app.route('/logs', methods=['GET'])
def fetch_logs():
    username = request.args.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    logs = get_recent_logs(username)
    return jsonify({"status": "success", "logs": logs}), 200

# Administrative command handler
def handle_command():
    while True:
        command = input("Enter command (/accept [username] or /deny [username] [reason]): ").strip()
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
        else:
            print(f"Invalid command: {command}")

# Run the Flask app
if __name__ == "__main__":
    init_db()
    Thread(target=handle_command, daemon=True).start()
    app.run(debug=False, port=5000)
