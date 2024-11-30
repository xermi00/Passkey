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
        # Create passkey table if not exists
        cursor.execute("""CREATE TABLE IF NOT EXISTS passkey (key TEXT)""")
        # Create registration table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                status TEXT,  -- 'pending', 'accepted', 'denied'
                reason TEXT DEFAULT NULL
            )
        """)
        # Insert default passkey if empty
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
def register():
    username = request.form.get('username')

    if not username or len(username) < 3 or len(username) > 15 or ' ' in username:
        return jsonify({"status": "failure", "message": "Invalid username format"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Insert username into the registration table
        cursor.execute("INSERT INTO registrations (username, status) VALUES (?, 'pending')", (username,))
        conn.commit()
        logging.info(f"Username '{username}' has attempted a registration.")
        return jsonify({"status": "success", "message": "Username submitted for approval"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "failure", "message": "Username already exists"}), 409
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Server error"}), 500
    finally:
        if conn:
            conn.close()
# Batch script routes
@app.route('/accept', methods=['POST'])
def accept_username():
    username = request.form.get('username')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE registrations SET status = 'accepted' WHERE username = ?", (username,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "Username not found"}), 404
        return jsonify({"status": "success", "message": f"Username '{username}' accepted"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Server error"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/deny', methods=['POST'])
def deny_username():
    username = request.form.get('username')
    reason = request.form.get('reason')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE registrations SET status = 'denied', reason = ? WHERE username = ?", (reason, username))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "Username not found"}), 404
        return jsonify({"status": "success", "message": f"Username '{username}' denied"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Server error"}), 500
    finally:
        if conn:
            conn.close()

# Route for Unity to check status
@app.route('/status', methods=['GET'])
def check_status():
    username = request.args.get('username')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status, reason FROM registrations WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            status, reason = result
            return jsonify({"status": "success", "registration_status": status, "reason": reason}), 200
        else:
            return jsonify({"status": "failure", "message": "Username not found"}), 404
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
