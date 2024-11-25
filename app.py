from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
from threading import Thread, Lock

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing
logging.basicConfig(level=logging.INFO)

# Database path
DB_PATH = "passkey.db"

# Thread-safe user data stores
user_lock = Lock()
PENDING_USERS = {}
APPROVED_USERS = {}
DENIED_USERS = {}
BANNED_USERS = {}

# Initialize the database
def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
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
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")

@app.route('/')
def home():
    return jsonify({"message": "Service is running!"})

@app.route('/ban', methods=['POST'])
def ban_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    with user_lock:
        if username in APPROVED_USERS:
            APPROVED_USERS.pop(username)
            BANNED_USERS[username] = True
            logging.info(f"Username {username} has been banned.")
            return jsonify({"status": "success", "message": f"Username {username} banned"}), 200
        return jsonify({"status": "failure", "message": "Username not found in approved list"}), 404

@app.route('/delusername', methods=['POST'])
def delete_username():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    with user_lock:
        if username in APPROVED_USERS:
            APPROVED_USERS.pop(username)
            logging.info(f"Username {username} has been deleted from approved list.")
            return jsonify({"status": "success", "message": f"Username {username} deleted"}), 200
        return jsonify({"status": "failure", "message": "Username not found in approved list"}), 404

@app.route('/delallusernames', methods=['POST'])
def delete_all_usernames():
    with user_lock:
        APPROVED_USERS.clear()
        logging.info("All usernames have been deleted from the approved list.")
    return jsonify({"status": "success", "message": "All approved usernames deleted"}), 200

@app.route('/unban', methods=['POST'])
def unban_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    with user_lock:
        if username in BANNED_USERS:
            BANNED_USERS.pop(username)
            logging.info(f"Username {username} has been unbanned.")
            return jsonify({"status": "success", "message": f"Username {username} unbanned"}), 200
        return jsonify({"status": "failure", "message": "Username not found in banned list"}), 404

@app.route('/kick', methods=['POST'])
def kick_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    with user_lock:
        if username in APPROVED_USERS:
            APPROVED_USERS.pop(username)
            logging.info(f"Username {username} has been kicked.")
            return jsonify({"status": "success", "message": f"Username {username} kicked"}), 200
        return jsonify({"status": "failure", "message": "Username not found in approved list"}), 404

@app.route('/verify', methods=['POST'])
def verify_passkey():
    user_passkey = request.form.get('passkey')
    if not user_passkey:
        return jsonify({"status": "failure", "message": "No passkey provided"}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key FROM passkey")
            stored_passkey = cursor.fetchone()

            if stored_passkey and user_passkey == stored_passkey[0]:
                return jsonify({"status": "success"}), 200
            return jsonify({"status": "failure", "message": "Incorrect passkey"}), 401
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500

@app.route('/update', methods=['POST'])
def update_passkey():
    new_passkey = request.form.get('passkey')
    if not new_passkey:
        return jsonify({"status": "failure", "message": "No passkey provided"}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE passkey SET key = ?", (new_passkey,))
            conn.commit()
        return jsonify({"status": "success", "message": "Passkey updated successfully"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400
    if " " in username or len(username) > 15:
        return jsonify({"status": "failure", "message": "Invalid username format"}), 400

    with user_lock:
        PENDING_USERS[username] = "Pending"
    logging.info(f"Username {username} submitted for approval.")
    return jsonify({"status": "success", "message": "Username submitted for approval"}), 200

@app.route('/status', methods=['GET'])
def status():
    username = request.args.get('username')
    with user_lock:
        if username in APPROVED_USERS:
            return jsonify({"status": "approved", "username": username}), 200
        elif username in PENDING_USERS:
            return jsonify({"status": "pending"}), 200
        elif username in DENIED_USERS:
            reason = DENIED_USERS.get(username, "No reason provided")
            return jsonify({"status": "denied", "message": reason}), 200
        return jsonify({"status": "not_found", "message": "Username not found"}), 404

@app.route('/approve', methods=['POST'])
def approve_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    with user_lock:
        if username in PENDING_USERS:
            PENDING_USERS.pop(username)
            APPROVED_USERS[username] = True
            logging.info(f"Username {username} has been approved.")
            return jsonify({"status": "success", "message": f"Username {username} approved"}), 200
        return jsonify({"status": "failure", "message": "Username not found in pending list"}), 404

@app.route('/deny', methods=['POST'])
def deny_user():
    username = request.form.get('username')
    reason = request.form.get('reason', "No reason provided")
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    with user_lock:
        if username in PENDING_USERS:
            PENDING_USERS.pop(username)
            DENIED_USERS[username] = reason
            logging.info(f"Username {username} denied: {reason}")
            return jsonify({"status": "success", "message": f"Username {username} denied for reason: {reason}"}), 200
        return jsonify({"status": "failure", "message": "Username not found in pending list"}), 404

# Command-line handler for administrative actions
def handle_command():
    while True:
        command = input("Enter command (/accept [username] or /deny [username] [reason]): ").strip()
        with user_lock:
            if command.startswith("/accept"):
                _, username = command.split(" ", 1)
                if username in PENDING_USERS:
                    PENDING_USERS.pop(username)
                    APPROVED_USERS[username] = True
                    logging.info(f"Username {username} approved.")
                else:
                    print(f"Username {username} not in pending list.")
            elif command.startswith("/deny"):
                parts = command.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: /deny [username] [reason]")
                    continue
                _, username, reason = parts
                if username in PENDING_USERS:
                    PENDING_USERS.pop(username)
                    DENIED_USERS[username] = reason
                    logging.info(f"Username {username} denied for reason: {reason}")
                else:
                    print(f"Username {username} not in pending list.")
            else:
                print("Invalid command.")

if __name__ == "__main__":
    init_db()
    Thread(target=handle_command, daemon=True).start()
    app.run(debug=False, host="0.0.0.0", port=5000)
