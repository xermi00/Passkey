from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)
DB_PATH = "users.db"

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                status TEXT,
                reason TEXT
            )
        """)
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
        return jsonify({"status": "failure", "message": "Username not provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Check if username already exists
        cursor.execute("SELECT status FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            if existing_user[0] == "accepted":
                return jsonify({"status": "failure", "message": "User already registered"}), 400
            return jsonify({"status": "failure", "message": "User registration pending or declined"}), 400

        cursor.execute("INSERT INTO users (username, status) VALUES (?, 'pending')", (username,))
        conn.commit()
        logging.info(f"Registration attempt by username: {username}")
        return jsonify({"status": "success", "message": "Registration request submitted"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/manage_user', methods=['POST'])
def manage_user():
    username = request.form.get('username')
    action = request.form.get('action')
    reason = request.form.get('reason', '')

    if not username or not action:
        return jsonify({"status": "failure", "message": "Invalid parameters"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"status": "failure", "message": "User not found"}), 404

        if action == "accept":
            cursor.execute("UPDATE users SET status = 'accepted', reason = NULL WHERE username = ?", (username,))
        elif action == "decline":
            cursor.execute("UPDATE users SET status = 'declined', reason = ? WHERE username = ?", (reason, username))
        else:
            return jsonify({"status": "failure", "message": "Invalid action"}), 400

        conn.commit()
        return jsonify({"status": "success", "message": f"User {action}ed"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/status', methods=['POST'])
def check_status():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "Username not provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status, reason FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"status": "failure", "message": "User not found"}), 404

        return jsonify({"status": "success", "user_status": user[0], "reason": user[1] or ""}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
