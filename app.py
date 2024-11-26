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

# User management stores
PENDING_USERS = {}
APPROVED_USERS = {}
DENIED_USERS = {}
BANNED_USERS = set()

# Utility Functions
def init_db():
    """
    Initialize the database and ensure the passkey table exists.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT PRIMARY KEY
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM passkey")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
            logging.info("Default passkey added.")
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        conn.close()

def is_valid_username(username):
    """
    Validate username format.
    - No spaces
    - Maximum length of 15 characters
    """
    return username and " " not in username and len(username) <= 15

# Routes
@app.route('/')
def home():
    return jsonify({"message": "Service is running!"})

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    if not is_valid_username(username):
        return jsonify({"status": "failure", "message": "Invalid username format"}), 400

    if username in PENDING_USERS or username in APPROVED_USERS:
        return jsonify({"status": "failure", "message": "Username already registered"}), 400

    logging.info(f"Registration request received for: {username}")
    PENDING_USERS[username] = "Pending"
    return jsonify({"status": "success", "message": "Registration submitted for approval"}), 200

@app.route('/approve', methods=['POST'])
def approve_user():
    username = request.form.get('username')
    if not username or username not in PENDING_USERS:
        return jsonify({"status": "failure", "message": "Username not found in pending list"}), 404

    PENDING_USERS.pop(username)
    APPROVED_USERS[username] = True
    logging.info(f"Approved username: {username}")
    return jsonify({"status": "success", "message": f"Username {username} approved"}), 200

@app.route('/deny', methods=['POST'])
def deny_user():
    username = request.form.get('username')
    reason = request.form.get('reason', "No reason provided")
    if not username or username not in PENDING_USERS:
        return jsonify({"status": "failure", "message": "Username not found in pending list"}), 404

    PENDING_USERS.pop(username)
    DENIED_USERS[username] = reason
    logging.info(f"Denied username: {username} for reason: {reason}")
    return jsonify({"status": "success", "message": f"Username {username} denied for reason: {reason}"}), 200

@app.route('/ban', methods=['POST'])
def ban_user():
    username = request.form.get('username')
    if not username or username not in APPROVED_USERS:
        return jsonify({"status": "failure", "message": "Username not found in approved list"}), 404

    BANNED_USERS.add(username)
    logging.info(f"Banned username: {username}")
    return jsonify({"status": "success", "message": f"Username {username} banned"}), 200

@app.route('/unban', methods=['POST'])
def unban_user():
    username = request.form.get('username')
    if not username or username not in BANNED_USERS:
        return jsonify({"status": "failure", "message": "Username not found in banned list"}), 404

    BANNED_USERS.remove(username)
    logging.info(f"Unbanned username: {username}")
    return jsonify({"status": "success", "message": f"Username {username} unbanned"}), 200

@app.route('/status', methods=['GET'])
def status():
    username = request.args.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if username in BANNED_USERS:
        return jsonify({"status": "banned"}), 200
    elif username in APPROVED_USERS:
        return jsonify({"status": "approved"}), 200
    elif username in PENDING_USERS:
        return jsonify({"status": "pending"}), 200
    elif username in DENIED_USERS:
        return jsonify({"status": "denied", "reason": DENIED_USERS[username]}), 200
    else:
        return jsonify({"status": "unknown", "message": "Username not found"}), 404

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "failure", "message": "Route not found"}), 404

# Run Server
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
