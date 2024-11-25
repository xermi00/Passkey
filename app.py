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

        # Create passkey table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey (
                key TEXT
            )
        """)
        logging.info("Passkey table initialized.")

        # Insert default passkey if the table is empty
        cursor.execute("SELECT COUNT(*) FROM passkey")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
            logging.info("Inserted default passkey.")

        # Create registrations table if it doesn't exist
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

# Register a new username
@app.route('/register', methods=['POST'])
def register_username():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    if len(username) > 15 or ' ' in username:
        return jsonify({"status": "failure", "message": "Invalid username. Ensure it is no more than 15 characters and contains no spaces."}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO registrations (username) VALUES (?)", (username,))
        conn.commit()
        logging.info(f"[{username}] has tried to register.")
        return jsonify({"status": "success", "message": "Registration request sent."}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "failure", "message": "Username already registered or pending approval."}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

# Notify player of registration status
@app.route('/notify', methods=['POST'])
def notify_status():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM registrations WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result is None:
            return jsonify({"status": "failure", "message": "No registration found for the provided username"}), 404

        status = result[0]
        logging.info(f"Notification for [{username}]: {status}.")
        return jsonify({"status": "success", "registration_status": status}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

# Admin command to accept or decline registration
@app.route('/admin', methods=['POST'])
def admin_command():
    command = request.form.get('command')

    if not command:
        return jsonify({"status": "failure", "message": "No command provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if command.startswith('/accept '):
            username = command.split('/accept ')[1]
            cursor.execute("UPDATE registrations SET status = 'accepted' WHERE username = ?", (username,))
            if cursor.rowcount == 0:
                return jsonify({"status": "failure", "message": f"No pending registration found for username: {username}"}), 404
            conn.commit()
            logging.info(f"Registration for [{username}] has been accepted.")
            return jsonify({"status": "success", "message": f"Accepted registration for {username}"}), 200

        elif command.startswith('/decline '):
            username = command.split('/decline ')[1]
            cursor.execute("DELETE FROM registrations WHERE username = ?", (username,))
            if cursor.rowcount == 0:
                return jsonify({"status": "failure", "message": f"No pending registration found for username: {username}"}), 404
            conn.commit()
            logging.info(f"Registration for [{username}] has been declined.")
            return jsonify({"status": "success", "message": f"Declined registration for {username}"}), 200

        else:
            return jsonify({"status": "failure", "message": "Invalid command."}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Initialize the database
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
