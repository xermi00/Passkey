from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing
logging.basicConfig(level=logging.INFO)

# Database path
DB_PATH = "passkey.db"

# Utility Functions
def init_db():
    """
    Initialize the database and ensure the required tables exist.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'banned'
                reason TEXT                              -- Reason for denial or banning
            )
        """)

        # Create passkey table for backward compatibility
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

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if not is_valid_username(username):
        return jsonify({"status": "failure", "message": "Invalid username format"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Insert or replace the user into the database
        cursor.execute("""
            INSERT OR REPLACE INTO users (username, status)
            VALUES (?, 'pending')
        """, (username,))
        conn.commit()

        logging.info(f"Username {username} registered for approval.")
        return jsonify({"status": "success", "message": "Username submitted for approval"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        conn.close()

@app.route('/status', methods=['GET'])
def status():
    username = request.args.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status, reason FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            status, reason = result
            response = {"status": status}
            if status in ["denied", "banned"]:
                response["message"] = reason
            return jsonify(response), 200
        else:
            return jsonify({"status": "not_found", "message": "Username not found"}), 404
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        conn.close()

@app.route('/ban', methods=['POST'])
def ban_user():
    username = request.form.get('username')
    reason = request.form.get('reason', "No reason provided")

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET status = 'banned', reason = ?
            WHERE username = ?
        """, (reason, username))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "Username not found"}), 404

        logging.info(f"Username {username} has been banned.")
        return jsonify({"status": "success", "message": f"Username {username} banned"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        conn.close()

@app.route('/unban', methods=['POST'])
def unban_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET status = 'approved', reason = NULL
            WHERE username = ?
        """, (username,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "Username not found"}), 404

        logging.info(f"Username {username} has been unbanned.")
        return jsonify({"status": "success", "message": f"Username {username} unbanned"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        conn.close()

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "failure", "message": "Route not found"}), 404

# Run Server
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
