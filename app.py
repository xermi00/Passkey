from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
from threading import Thread
import os

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

# Render.com log file path (or API if applicable)
RENDER_LOG_PATH = "/path/to/render/logs.txt"  # Replace with actual path or API URL

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

# Check unban status from Render logs
def check_unban_status():
    logging.info("Unban detection thread started.")
    while True:
        try:
            # Simulating log file or API reading
            if os.path.exists(RENDER_LOG_PATH):
                with open(RENDER_LOG_PATH, "r") as log_file:
                    logs = log_file.readlines()

                for username in list(BANNED_USERS.keys()):
                    if any(f"{username} unbanned" in log for log in logs):
                        logging.info(f"Detected unban for {username} in logs.")
                        BANNED_USERS.pop(username, None)
                        update_user_status(username, "unbanned")
        except Exception as e:
            logging.error(f"Error while checking unban status: {e}")

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

@app.route('/verify', methods=['GET', 'POST'])
def verify_passkey():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if request.method == 'GET':
            # Handle GET request: Retrieve the stored passkey
            cursor.execute("SELECT key FROM passkey")
            stored_passkey = cursor.fetchone()

            if stored_passkey:
                return jsonify({"status": "success", "passkey": stored_passkey[0]}), 200
            else:
                return jsonify({"status": "failure", "message": "No passkey stored"}), 404

        elif request.method == 'POST':
            # Handle POST request: Verify provided passkey
            user_passkey = request.form.get('passkey')

            if not user_passkey:
                return jsonify({"status": "failure", "message": "No passkey provided"}), 400

            cursor.execute("SELECT key FROM passkey")
            stored_passkey = cursor.fetchone()

            if stored_passkey and stored_passkey[0] == user_passkey:
                return jsonify({"status": "success", "message": "Passkey verified"}), 200
            else:
                return jsonify({"status": "failure", "message": "Invalid passkey"}), 401
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Server error"}), 500
    finally:
        if conn:
            conn.close()

# Passkey update
@app.route('/update', methods=['POST'])
def update_passkey():
    new_passkey = request.form.get('passkey')

    if not new_passkey:
        return jsonify({"status": "failure", "message": "No passkey provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE passkey SET key = ?", (new_passkey,))
        conn.commit()
        return jsonify({"status": "success", "message": "Passkey updated successfully"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

# Register a new user
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

# Approve a user
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

# Deny a user
@app.route('/deny', methods=['POST'])
def deny_user():
    username = request.form.get('username')
    reason = request.form.get('reason', "No reason provided")

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if username in PENDING_USERS:
        PENDING_USERS.pop(username, None)
        DENIED_USERS[username] = reason
        update_user_status(username, "denied")
        logging.info(f"Username {username} has been denied: {reason}")
        return jsonify({"status": "success", "message": f"Username {username} denied for reason: {reason}"}), 200
    else:
        return jsonify({"status": "failure", "message": f"Username {username} not found in pending list"}), 404

# Administrative command handler
def handle_command():
    while True:
        command = input("Enter command (/accept [username] or /deny [username]): ").strip()
        if command.startswith("/accept"):
            _, username = command.split(" ")
            if username in PENDING_USERS:
                PENDING_USERS.pop(username, None)
                APPROVED_USERS[username] = True
                logging.info(f"Username {username} has been approved.")
            else:
                logging.info(f"Username {username} not found in pending list.")
        elif command.startswith("/deny"):
            _, username = command.split(" ")
            if username in PENDING_USERS:
                PENDING_USERS.pop(username, None)
                DENIED_USERS[username] = "No reason provided"
                logging.info(f"Username {username} has been denied.")
            else:
                logging.info(f"Username {username} not found in pending list.")
        else:
            logging.info("Unknown command.")

@app.route('/check_passkey', methods=['GET'])
def check_passkey():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT key FROM passkey")
        stored_passkey = cursor.fetchone()

        if stored_passkey:
            return jsonify({"status": "success", "message": stored_passkey[0]}), 200
        else:
            return jsonify({"status": "failure", "message": "No passkey found"}), 404
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    init_db()
    # Start the unban detection thread
    unban_thread = Thread(target=check_unban_status, daemon=True)
    unban_thread.start()
    # Start the administrative command thread
    admin_thread = Thread(target=handle_command, daemon=True)
    admin_thread.start()
    app.run(host='0.0.0.0', port=5000)
