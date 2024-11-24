app = Flask(__name__)
DB_PATH = "passkey.db"

# Verify the passkey
@app.route('/verify', methods=['POST'])
def verify_passkey():
    user_passkey = request.form.get('passkey')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key FROM passkey")
    stored_passkey = cursor.fetchone()[0]
    conn.close()

    if user_passkey == stored_passkey:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "failure"}), 401

# Update the passkey
@app.route('/update', methods=['POST'])
def update_passkey():
    new_passkey = request.form.get('passkey')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE passkey SET key = ?", (new_passkey,))
    conn.commit()
    conn.close()
    return jsonify({"status": "passkey updated"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


# A passkey.db file


import sqlite3

# Path to your database file
DB_PATH = "passkey.db"

# Initialize the database and create the passkey table
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passkey (
            key TEXT
        )
    """)

    # Insert an initial passkey if the table is empty
    cursor.execute("SELECT COUNT(*) FROM passkey")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO passkey (key) VALUES ('default_passkey')")
        print("Inserted default passkey.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
