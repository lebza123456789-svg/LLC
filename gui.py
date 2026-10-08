from flask import Flask
import sqlite3

app = Flask(__name__)

def get_db():
    connection = sqlite3.connect("llc")
    connection.row_factory = sqlite3.Row
    return connection

@app.route("/def")
def home():
    connection = get_db()

    users = connection.execute(
        "SELECT * FROM users"
    ).fetchall

    connection.close()

    return str([dict(user) for user in users])

if __name__ == "__main__":
    app.run(debug=True)
