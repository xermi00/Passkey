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
        # Create tables if they don't exist
        cursor.execute("""CREATE TABLE IF NOT EXISTS passkey (key TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (username TEXT, status TEXT, reason TEXT)""")
        # Ensure default passkey
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

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')

    if not username or len(username) < 3 or len(username) > 15 or ' ' in username:
        return jsonify({"status": "failure", "message": "Invalid username"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({"status": "failure", "message": "Username already exists"}), 409

        cursor.execute("INSERT INTO users (username, status, reason) VALUES (?, ?, ?)", 
                       (username, 'pending', None))
        conn.commit()
        logging.info(f"{username} has attempted a registration.")
        return jsonify({"status": "success", "message": "Registration submitted"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Server error"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/review', methods=['POST'])
def review_user():
    command = request.form.get('command')
    if not command:
        return jsonify({"status": "failure", "message": "No command provided"}), 400

    parts = command.split()
    if len(parts) < 2:
        return jsonify({"status": "failure", "message": "Invalid command format"}), 400

    action = parts[0]
    username = parts[1]
    reason = ' '.join(parts[2:]) if len(parts) > 2 else None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"status": "failure", "message": "User not found"}), 404

        if action == '/accept':
            cursor.execute("UPDATE users SET status = ? WHERE username = ?", ('accepted', username))
            conn.commit()
            return jsonify({"status": "success", "message": f"Accepted {username}"}), 200
        elif action == '/deny':
            if not reason:
                return jsonify({"status": "failure", "message": "Reason required for denial"}), 400
            cursor.execute("UPDATE users SET status = ?, reason = ? WHERE username = ?", 
                           ('denied', reason, username))
            conn.commit()
            return jsonify({"status": "success", "message": f"Denied {username}"}), 200
        else:
            return jsonify({"status": "failure", "message": "Unknown command"}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Server error"}), 500
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
