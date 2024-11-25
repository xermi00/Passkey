from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Database path
DB_PATH = "passkey.db"

# Data stores
PENDING_USERS = {}
APPROVED_USERS = {}
DENIED_USERS = {}
BANNED_USERS = {}

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT
            )
        """)
        # Insert default passkey if table is empty
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

# Routes
@app.route('/')
def home():
    return jsonify({"message": "Service is running!"})

@app.route('/ban', methods=['POST'])
def ban_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400
    if username in APPROVED_USERS:
        APPROVED_USERS.pop(username)
        BANNED_USERS[username] = True
        logging.info(f"Banned user: {username}")
        return jsonify({"status": "success", "message": f"{username} has been banned"}), 200
    return jsonify({"status": "failure", "message": "User not found in approved list"}), 404

@app.route('/unban', methods=['POST'])
def unban_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400
    if username in BANNED_USERS:
        BANNED_USERS.pop(username)
        logging.info(f"Unbanned user: {username}")
        return jsonify({"status": "success", "message": f"{username} has been unbanned"}), 200
    return jsonify({"status": "failure", "message": "User not found in banned list"}), 404

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
        if not stored_passkey or user_passkey != stored_passkey[0]:
            return jsonify({"status": "failure", "message": "Incorrect passkey"}), 401
        return jsonify({"status": "success"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error"}), 500
    finally:
        if conn:
            conn.close()

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
        logging.info("Passkey updated.")
        return jsonify({"status": "success", "message": "Passkey updated successfully"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    if not username or " " in username or len(username) > 15:
        return jsonify({"status": "failure", "message": "Invalid username format"}), 400
    PENDING_USERS[username] = "Pending"
    logging.info(f"User registered: {username}")
    return jsonify({"status": "success", "message": "User registered"}), 200

@app.route('/status', methods=['GET'])
def status():
    username = request.args.get('username')
    if username in APPROVED_USERS:
        return jsonify({"status": "approved"}), 200
    if username in PENDING_USERS:
        return jsonify({"status": "pending"}), 200
    if username in DENIED_USERS:
        return jsonify({"status": "denied", "message": DENIED_USERS[username]}), 200
    return jsonify({"status": "not_found"}), 404

@app.route('/approve', methods=['POST'])
def approve_user():
    username = request.form.get('username')
    if not username or username not in PENDING_USERS:
        return jsonify({"status": "failure", "message": "User not found in pending list"}), 404
    PENDING_USERS.pop(username)
    APPROVED_USERS[username] = True
    logging.info(f"User approved: {username}")
    return jsonify({"status": "success", "message": "User approved"}), 200

@app.route('/deny', methods=['POST'])
def deny_user():
    username = request.form.get('username')
    reason = request.form.get('reason', "No reason provided")
    if not username or username not in PENDING_USERS:
        return jsonify({"status": "failure", "message": "User not found in pending list"}), 404
    PENDING_USERS.pop(username)
    DENIED_USERS[username] = reason
    logging.info(f"User denied: {username} - {reason}")
    return jsonify({"status": "success", "message": "User denied"}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
