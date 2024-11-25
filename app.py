from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)
DB_PATH = "passkey.db"

logging.basicConfig(level=logging.INFO)


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


@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')
    if not username or len(username) > 15 or " " in username:
        return jsonify({"status": "failure", "message": "Invalid username"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, status) VALUES (?, ?)", (username, 'pending'))
        conn.commit()
        logging.info(f"{username} has tried to register.")
        return jsonify({"status": "success", "message": "Registration request submitted."}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "failure", "message": "Username already exists"}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/commands', methods=['POST'])
def handle_commands():
    command = request.form.get('command')
    if not command:
        return jsonify({"status": "failure", "message": "No command provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if command.startswith("/accept"):
            _, username = command.split()
            cursor.execute("UPDATE users SET status = 'accepted', reason = NULL WHERE username = ?", (username,))
            if cursor.rowcount > 0:
                conn.commit()
                return jsonify({"status": "success", "message": f"{username} accepted."}), 200
            else:
                return jsonify({"status": "failure", "message": f"{username} not found."}), 404

        elif command.startswith("/decline"):
            _, username = command.split()
            reason = request.form.get('reason')
            if not reason:
                return jsonify({"status": "failure", "message": "Decline reason required."}), 400
            cursor.execute("UPDATE users SET status = 'declined', reason = ? WHERE username = ?", (reason, username))
            if cursor.rowcount > 0:
                conn.commit()
                return jsonify({"status": "success", "message": f"{username} declined."}), 200
            else:
                return jsonify({"status": "failure", "message": f"{username} not found."}), 404

        elif command.startswith("/changeuser"):
            _, old_username, new_username = command.split()
            if len(new_username) > 15 or " " in new_username:
                return jsonify({"status": "failure", "message": "Invalid new username"}), 400
            cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
            if cursor.rowcount > 0:
                conn.commit()
                return jsonify({"status": "success", "message": f"Username changed to {new_username}."}), 200
            else:
                return jsonify({"status": "failure", "message": f"{old_username} not found."}), 404
        else:
            return jsonify({"status": "failure", "message": "Unknown command"}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
