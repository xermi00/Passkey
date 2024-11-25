from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing
DB_PATH = "passkey.db"

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize the database if it doesn't exist
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT UNIQUE,
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

@app.route('/')
def home():
    return jsonify({"message": "Registration service is running!"})

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')
    if not username or len(username) > 15 or ' ' in username:
        return jsonify({"status": "failure", "message": "Invalid username"}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (username, status) VALUES (?, ?)", (username, 'pending'))
        conn.commit()
        logging.info(f"{username} has tried to register.")
        return jsonify({"status": "success", "message": "Registration pending approval"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/accept/<username>', methods=['POST'])
def accept_user(username):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'accepted' WHERE username = ?", (username,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": f"User {username} not found"}), 404
        return jsonify({"status": "success", "message": f"User {username} accepted"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/decline/<username>', methods=['POST'])
def decline_user(username):
    reason = request.form.get('reason')
    if not reason:
        return jsonify({"status": "failure", "message": "Decline reason is required"}), 400
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'declined', reason = ? WHERE username = ?", (reason, username))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": f"User {username} not found"}), 404
        return jsonify({"status": "success", "message": f"User {username} declined"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/changeuser', methods=['POST'])
def change_user():
    old_username = request.form.get('old_username')
    new_username = request.form.get('new_username')
    if not old_username or not new_username or len(new_username) > 15 or ' ' in new_username:
        return jsonify({"status": "failure", "message": "Invalid username"}), 400
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": f"User {old_username} not found"}), 404
        return jsonify({"status": "success", "message": f"Username changed to {new_username}"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
