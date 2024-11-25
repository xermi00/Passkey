from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

DB_PATH = "passkey.db"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the database if it doesn't exist
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create the passkey table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT NOT NULL
            )
        """)
        logging.info("Passkey table initialized.")

        # Insert default passkey if the table is empty
        cursor.execute("SELECT COUNT(*) FROM passkey")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
            logging.info("Inserted default passkey.")

        # Create the registrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        """)
        logging.info("Registrations table initialized.")

        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

# Root route
@app.route('/')
def home():
    return jsonify({"message": "Passkey verification and registration service is running!"})

# Verify the passkey
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

# Update the passkey
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

# Register a user
@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "Username is required"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the username already exists
        cursor.execute("SELECT * FROM registrations WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({"status": "failure", "message": "Username already exists"}), 409

        # Insert the new username with a pending status
        cursor.execute("INSERT INTO registrations (username, status) VALUES (?, 'pending')", (username,))
        conn.commit()
        return jsonify({"status": "success", "message": "Registration request submitted"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

# Notify about registration
@app.route('/notify', methods=['POST'])
def notify_admin():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "Username is required"}), 400

    # Simulate notification (e.g., send to admin console, email, etc.)
    logging.info(f"Notification: {username} has tried to register.")
    return jsonify({"status": "success", "message": "Notification sent"}), 200

# Process registration actions
@app.route('/process_registration', methods=['POST'])
def process_registration():
    username = request.form.get('username')
    action = request.form.get('action')  # 'accept' or 'decline'

    if not username or action not in ['accept', 'decline']:
        return jsonify({"status": "failure", "message": "Invalid username or action"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the username exists
        cursor.execute("SELECT * FROM registrations WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"status": "failure", "message": "Username not found"}), 404

        # Update the user's status based on the action
        new_status = "accepted" if action == "accept" else "declined"
        cursor.execute("UPDATE registrations SET status = ? WHERE username = ?", (new_status, username))
        conn.commit()

        return jsonify({"status": "success", "message": f"User '{username}' has been {new_status}"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

# Run the app
if __name__ == "__main__":
    # Initialize the database
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
