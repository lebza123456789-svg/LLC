from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from werkzeug.utils import secure_filename 
import uuid
import os

from flask import jsonify

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
    connection = get_db()

    user_id = session.get("user_id")

    posts = connection.execute(
        """
        SELECT
            posts.id,
            posts.content,
            posts.picture,
            posts.posted_at,
            users.username,
            (
                SELECT COUNT(*)
                FROM post_likes
                WHERE post_likes.post_id = posts.id
            ) AS like_count,
            (
                SELECT COUNT(*)
                FROM post_likes
                WHERE post_likes.post_id = posts.id
                AND post_likes.user_id = ?
            ) AS liked_by_me
        FROM posts
        LEFT JOIN users ON users.id = posts.user_id
        ORDER BY posts.posted_at DESC, posts.id DESC
        LIMIT 30
        """,
        (user_id,)
    ).fetchall()

    
    # Top 5 car owners by likes received on their posts
    leaderboard = connection.execute("""
        SELECT
            users.username,
            cars.description,
            COUNT(post_likes.id) AS likes
        FROM cars
        JOIN users ON users.id = cars.owner_id
        LEFT JOIN posts ON posts.user_id = users.id
        LEFT JOIN post_likes ON post_likes.post_id = posts.id
        GROUP BY cars.id, users.username, cars.description
        ORDER BY likes DESC, cars.id ASC
        LIMIT 5
    """).fetchall()

    # Upcoming events
    upcoming_events = connection.execute("""
        SELECT name, date, location
        FROM events
        WHERE date >= date('now')
        ORDER BY date ASC
        LIMIT 3
    """).fetchall()


    connection.close()

    return render_template(
    "home.html",
    posts=posts,
    leaderboard=leaderboard,
    upcoming_events=upcoming_events
)

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




# Where uploaded post photos will be saved
UPLOAD_FOLDER = Path(__file__).resolve().parent / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


@app.route("/create-post", methods=["GET", "POST"])
def create_post():
    # Only logged-in users may create posts
    if "user_id" not in session:
        flash("Please log in before creating a post.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        picture = request.files.get("picture")

        if not picture or not picture.filename:
            flash("Please select a car photo.", "error")
            return redirect(url_for("create_post"))

        filename = secure_filename(picture.filename)
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if extension not in ALLOWED_EXTENSIONS:
            flash("Use a JPG, PNG or WEBP image.", "error")
            return redirect(url_for("create_post"))

        # Generate a unique filename to avoid overwriting other photos
        saved_filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = UPLOAD_FOLDER / saved_filename
        picture.save(file_path)

        connection = get_db()

        try:
            connection.execute(
                """
                INSERT INTO posts (user_id, content, picture)
                VALUES (?, ?, ?)
                """,
                (
                    session["user_id"],
                    content,
                    f"uploads/{saved_filename}"
                )
            )
            connection.commit()
        except Exception:
            file_path.unlink(missing_ok=True)
            raise
        finally:
            connection.close()

        flash("Your post has been published!", "success")
        return redirect(url_for("home"))

    return render_template("create_post.html")



from flask import jsonify

@app.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in to like posts.",
            "login_required": True
        }), 401

    user_id = session["user_id"]
    connection = get_db()

    try:
        post = connection.execute(
            "SELECT id FROM posts WHERE id = ?",
            (post_id,)
        ).fetchone()

        if post is None:
            return jsonify({
                "success": False,
                "message": "Post not found."
            }), 404

        existing_like = connection.execute(
            """
            SELECT id FROM post_likes
            WHERE post_id = ? AND user_id = ?
            """,
            (post_id, user_id)
        ).fetchone()

        if existing_like:
            connection.execute(
                """
                DELETE FROM post_likes
                WHERE post_id = ? AND user_id = ?
                """,
                (post_id, user_id)
            )
            liked = False
        else:
            connection.execute(
                """
                INSERT INTO post_likes (post_id, user_id)
                VALUES (?, ?)
                """,
                (post_id, user_id)
            )
            liked = True

        connection.commit()

        like_count = connection.execute(
            "SELECT COUNT(*) FROM post_likes WHERE post_id = ?",
            (post_id,)
        ).fetchone()[0]

        return jsonify({
            "success": True,
            "liked": liked,
            "like_count": like_count
        })

    finally:
        connection.close()




if __name__ == "__main__":
    app.run(debug=True)
    
