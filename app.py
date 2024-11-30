from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing
logging.basicConfig(level=logging.INFO)

# Database path
DB_PATH = "passkey.db"

# Initialize the database if it doesn't exist
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                username TEXT PRIMARY KEY,
                status TEXT, -- 'pending', 'accepted', 'denied'
                denial_reason TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    if username:
        logging.info(f"{username} has attempted a registration.")
        return jsonify({"status": "success", "message": "Registration received"}), 200
    else:
        return jsonify({"status": "failure", "message": "No username provided"}), 400
        
@app.route('/manage', methods=['GET', 'POST'])
def manage_registration():
    username = request.args.get('username') or request.form.get('username')
    action = request.args.get('action') or request.form.get('action')
    reason = request.form.get('reason', '')

    if not username or not action:
        return jsonify({"status": "failure", "message": "Invalid data"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the username exists
        cursor.execute("SELECT status FROM registrations WHERE username = ?", (username,))
        existing = cursor.fetchone()

        if action == "accept":
            if existing:
                cursor.execute("UPDATE registrations SET status = 'accepted', denial_reason = NULL WHERE username = ?", (username,))
            else:
                cursor.execute("INSERT INTO registrations (username, status) VALUES (?, 'accepted')", (username,))
            conn.commit()
            return jsonify({"status": "success", "message": f"{username} has been accepted."}), 200

        elif action == "deny":
            if existing:
                cursor.execute("UPDATE registrations SET status = 'denied', denial_reason = ? WHERE username = ?", (reason, username))
            else:
                cursor.execute("INSERT INTO registrations (username, status, denial_reason) VALUES (?, 'denied', ?)", (username, reason))
            conn.commit()
            return jsonify({"status": "success", "message": f"{username} has been denied."}), 200

        elif action == "check_accept":
            if existing and existing[0] == "accepted":
                return jsonify({"status": "success", "message": "accepted"}), 200
            return jsonify({"status": "failure", "message": "not accepted"}), 200

        elif action == "check_deny":
            if existing and existing[0] == "denied":
                cursor.execute("SELECT denial_reason FROM registrations WHERE username = ?", (username,))
                reason = cursor.fetchone()[0]
                return jsonify({"status": "success", "message": "denied", "data": reason}), 200
            return jsonify({"status": "failure", "message": "not denied"}), 200

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()




# Root route
@app.route('/')
def home():
    return jsonify({"message": "Service is running!"})

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
    app.run(host='0.0.0.0', port=5000)
