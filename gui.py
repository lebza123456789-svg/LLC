from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path 
import os

app = Flask(__name__)

#secret key
app.config["SECRET_KEY"] = os.environ.get("LLC_SECRET_KEY", "dev-only-change-this-key")
DATABASE = Path(__file__).resolve().parent / "llc"

def get_db():
    connection = sqlite3.connect("llc")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = on")
    return connection


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username","").strip()
        password = request.form.get("password", "")

        connection = get_db()
        try:
            user = connection.execute("""
            SELECT id, username, email, password_hash
            FROM users
            WHERE username = ? COLLATE NOCASE
            OR email = ? COLLATE NOCASE """, (username_or_email, username_or_email)).fetchone()

        except sqlite3.Error:
            app.logger.exception("Login database error")
            flash("Login is temporarily unavaible", "error")
            return render_template("login.html")

        finally:
            connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            flash("Welcome back to LLC!", "success")
            return redirect(url_for("home"))
        flash("Incorrect username/email or password.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        email = request.form.get("email","").lower()
        password = request.form.get("password","")
        confirm_password = request.form.get("confirm_password","")

        if not username or not email or not password:
            flash("Please fill in all required fields", "error")
            return render_template("register.html")

        if len(username) < 3 or len(username) > 30:
            flash("Username must be between 3 and 30 characters.","error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Your password must contain at least 8 characters.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Your password must match", "error")
            return render_template("register.html")

        connection = get_db()

        try:
            existing_user = connection.execute(""" SELECT id FROM users 
            WHERE username = ? OR email = ? """,(username, email)).fetchone()

            if existing_user:
                flash("That username or email is already registered", "error")
                return render_template("register.html")

            password_hash = generate_password_hash(password)

            connection.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)""", (username, email, password_hash))
            connection.commit()

            flash("Account created! You can now login", "success")
            return redirect(url_for("login"))

        except sqlite3.Error:
            app.logger.exception("Registration database error")
            flash("Registration could not be complete. Check your users table cloumns.", "error")

        finally:
            connection.close()

    return render_template("register.html")






if __name__ == "__main__":
    app.run(debug=True)
    
