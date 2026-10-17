from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from werkzeug.utils import secure_filename 
import uuid
import os
from datetime import  date

from flask import jsonify

app = Flask(__name__)

#secret key
app.config["SECRET_KEY"] = os.environ.get("LLC_SECRET_KEY", "dev-only-change-this-key")
DATABASE = Path(__file__).resolve().parent / "llc"

def get_db():
    connection = sqlite3.connect("llc")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
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

@app.route("/profile/<username>")
def profile(username):
    connection = get_db()

    try:
        user = connection.execute(
            """
            SELECT id, username, profile_picture, location, created_at
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if user is None:
            return "User not found", 404

        user_id = user["id"]

        posts = connection.execute(
            """
            SELECT posts.id, posts.content, posts.picture, posts.posted_at,
                   (
                       SELECT COUNT(*)
                       FROM post_likes
                       WHERE post_likes.post_id = posts.id
                   ) AS like_count
            FROM posts
            WHERE posts.user_id = ?
            ORDER BY posts.posted_at DESC, posts.id DESC
            """,
            (user_id,)
        ).fetchall()

        cars = connection.execute(
            """
            SELECT id, description, picture, created_at
            FROM garage
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        likes_received = connection.execute(
            """
            SELECT COUNT(*)
            FROM post_likes
            JOIN posts ON posts.id = post_likes.post_id
            WHERE posts.user_id = ?
            """,
            (user_id,)
        ).fetchone()[0]

        return render_template(
            "profile.html",
            user=user,
            posts=posts,
            cars=cars,
            likes_received=likes_received,
            is_own_profile=session.get("user_id") == user_id
        )

    finally:
        connection.close()


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/garage")
def garage():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    cars = connection.execute("""
        SELECT id, description, picture, created_at
        FROM garage
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template("garage.html", cars=cars)


@app.route("/garage/add", methods=["POST"])
def add_garage_car():
    if "user_id" not in session:
        return redirect(url_for("login"))

    description = request.form.get("description", "").strip()
    picture = request.files.get("picture")

    if not description:
        flash("Please add a description for your car.")
        return redirect(url_for("garage"))

    if not picture or not picture.filename:
        flash("Please choose a car photo.")
        return redirect(url_for("garage"))

    if not allowed_file(picture.filename):
        flash("Use a JPG, JPEG, PNG or WEBP image.")
        return redirect(url_for("garage"))

    upload_folder = Path(app.root_path) / "static" / "uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)

    extension = secure_filename(picture.filename).rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    picture.save(upload_folder / filename)

    connection = get_db()

    try:
        connection.execute("""
            INSERT INTO garage (user_id, description, picture)
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            description,
            f"uploads/{filename}"
        ))

        connection.commit()
    except Exception:
        connection.rollback()
        (upload_folder / filename).unlink(missing_ok=True)
        raise
    finally:
        connection.close()

    flash("Your car was added to your garage!")
    return redirect(url_for("garage"))

@app.route("/clans")
def clans():
    connection = get_db()

    user_id = session.get("user_id")

    all_clans = connection.execute("""
        SELECT
            c.id,
            c.name,
            c.description,
            c.profile_picture,
            COUNT(DISTINCT cm.user_id) AS member_count,
            EXISTS (
                SELECT 1
                FROM clan_members mine
                WHERE mine.clan_id = c.id
                  AND mine.user_id = ?
            ) AS is_member
        FROM clans c
        LEFT JOIN clan_members cm ON cm.clan_id = c.id
        GROUP BY c.id
        ORDER BY c.name COLLATE NOCASE
    """, (user_id,)).fetchall()

    connection.close()

    return render_template("clans.html", clans=all_clans)

@app.route("/clans/create", methods=["POST"])
def create_clan():
    if "user_id" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name or not description:
        flash("Enter a clan name and description.")
        return redirect(url_for("clans"))

    connection = get_db()

    try:
        cursor = connection.execute("""
            INSERT INTO clans (name, description, owner_id)
            VALUES (?, ?, ?)
        """, (name, description, session["user_id"]))

        clan_id = cursor.lastrowid

        connection.execute("""
            INSERT INTO clan_members (clan_id, user_id)
            VALUES (?, ?)
        """, (clan_id, session["user_id"]))

        connection.commit()

    except sqlite3.IntegrityError:
        connection.rollback()
        flash("That clan name already exists.")
        return redirect(url_for("clans"))

    finally:
        connection.close()

    flash("Clan created successfully!")
    return redirect(url_for("clans"))

@app.route("/clans/<int:clan_id>")
def clan_detail(clan_id):
    connection = get_db()

    clan = connection.execute("""
        SELECT
            c.*,
            COUNT(DISTINCT cm.user_id) AS member_count
        FROM clans c
        LEFT JOIN clan_members cm ON cm.clan_id = c.id
        WHERE c.id = ?
        GROUP BY c.id
    """, (clan_id,)).fetchone()

    if clan is None:
        connection.close()
        abort(404)

    members = connection.execute("""
        SELECT u.id, u.username, u.profile_picture
        FROM clan_members cm
        JOIN users u ON u.id = cm.user_id
        WHERE cm.clan_id = ?
        ORDER BY u.username
    """, (clan_id,)).fetchall()

    events = connection.execute("""
        SELECT id, name, date, location, picture
        FROM events
        WHERE clan_id = ?
        ORDER BY date(date) ASC
    """, (clan_id,)).fetchall()

    connection.close()

    return render_template(
        "clan_detail.html",
        clan=clan,
        members=members,
        events=events
    )



# FUNCTION FOR THE EVENT PSOTING 

ALLOWED_EVENT_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def event_image_allowed(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EVENT_EXTENSIONS
    )


def get_event_or_404(connection, event_id):
    event = connection.execute("""
        SELECT
            e.id,
            e.clan_id,
            e.name,
            e.description,
            e.date,
            e.location,
            e.picture,
            e.created_at,
            c.name AS clan_name
        FROM events e
        JOIN clans c ON c.id = e.clan_id
        WHERE e.id = ?
    """, (event_id,)).fetchone()

    if event is None:
        abort(404)

    return event


@app.route("/events")
def events():
    connection = get_db()

    try:
        upcoming_events = connection.execute("""
            SELECT
                e.id,
                e.name,
                e.description,
                e.date,
                e.location,
                e.picture,
                c.name AS clan_name
            FROM events e
            JOIN clans c ON c.id = e.clan_id
            WHERE date(e.date) >= date('now', 'localtime')
            ORDER BY date(e.date) ASC, e.id DESC
        """).fetchall()
    finally:
        connection.close()

    return render_template(
        "events.html",
        events=upcoming_events
    )


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    connection = get_db()

    try:
        event = get_event_or_404(connection, event_id)
    finally:
        connection.close()

    return render_template(
        "event_detail.html",
        event=event
    )


@app.route(
    "/clans/<int:clan_id>/events/create",
    methods=["GET", "POST"]
)
def create_event(clan_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    try:
        clan = connection.execute("""
            SELECT id, name, owner_id
            FROM clans
            WHERE id = ?
        """, (clan_id,)).fetchone()

        if clan is None:
            abort(404)

        # Only the clan owner may create an event.
        if clan["owner_id"] != session["user_id"]:
            abort(403)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            description = request.form.get(
                "description", ""
            ).strip()
            event_date = request.form.get("date", "").strip()
            location = request.form.get("location", "").strip()
            picture = request.files.get("picture")

            if not all([name, description, event_date, location]):
                flash("Please complete all event fields.")
                return render_template(
                    "create_event.html", clan=clan
                )

            try:
                parsed_date = date.fromisoformat(event_date)
            except ValueError:
                flash("Please enter a valid event date.")
                return render_template(
                    "create_event.html",
                    clan=clan,
                    today=date.today().isoformat()
                )

            if parsed_date < date.today():
                flash("An event date cannot be in the past.")
                return render_template(
                    "create_event.html", clan=clan
                )

            if len(name) > 120 or len(location) > 200:
                flash("The event name or location is too long.")
                return render_template(
                    "create_event.html", clan=clan
                )

            if len(description) > 5000:
                flash("The description must be 5000 characters or less.")
                return render_template(
                    "create_event.html", clan=clan
                )

            if not picture or not picture.filename:
                flash("Please upload an event photo.")
                return render_template(
                    "create_event.html", clan=clan
                )

            if not event_image_allowed(picture.filename):
                flash("Use a JPG, JPEG, PNG or WEBP photo.")
                return render_template(
                    "create_event.html", clan=clan
                )

            upload_folder = (
                Path(app.root_path) / "static" / "uploads"
            )
            upload_folder.mkdir(parents=True, exist_ok=True)

            extension = secure_filename(
                picture.filename
            ).rsplit(".", 1)[1].lower()

            filename = f"{uuid.uuid4().hex}.{extension}"
            saved_path = upload_folder / filename
            picture_saved = False

            try:
                picture.save(saved_path)
                picture_saved = True

                cursor = connection.execute("""
                    INSERT INTO events (
                        clan_id,
                        name,
                        description,
                        date,
                        location,
                        picture
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    clan_id,
                    name,
                    description,
                    event_date,
                    location,
                    f"uploads/{filename}"
                ))

                connection.commit()
                new_event_id = cursor.lastrowid

            except Exception:
                connection.rollback()

                if picture_saved:
                    saved_path.unlink(missing_ok=True)

                raise

            flash("Your clan event has been created!")
            return redirect(
                url_for(
                    "event_detail",
                    event_id=new_event_id
                )
            )

        return render_template(
            "create_event.html",
            clan=clan,
            today=date.today().isoformat()
        )
    finally:
        connection.close()


if __name__ == "__main__":
    app.run(debug=True)
    
