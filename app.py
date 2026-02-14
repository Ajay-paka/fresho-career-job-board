<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret123")


# ---------------- DATABASE HELPER ---------------- #

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DATABASE ---------------- #

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        skills TEXT,
        experience TEXT,
        salary TEXT,
        job_type TEXT,
        description TEXT,
        contact TEXT,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


init_db()

@app.route('/google069cb765d388000f.html')
def google_verification():
    return app.send_static_file('google069cb765d388000f.html')

@app.route("/sitemap.xml", methods=["GET"])
def sitemap():

    conn = get_db()
    jobs = conn.execute("SELECT id FROM jobs").fetchall()
    conn.close()

    urls = []

    # Home page (public version)
    urls.append("https://fresho-career.onrender.com/")

    # Job detail pages
    for job in jobs:
        urls.append(f"https://fresho-career.onrender.com/job/{job['id']}")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in urls:
        xml.append("<url>")
        xml.append(f"<loc>{url}</loc>")
        xml.append("<changefreq>daily</changefreq>")
        xml.append("<priority>0.8</priority>")
        xml.append("</url>")

    xml.append("</urlset>")

    return "\n".join(xml), 200, {'Content-Type': 'application/xml'}


# ---------------- ROLE DECORATOR ---------------- #

def recruiter_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "recruiter":
            return abort(403)
        return f(*args, **kwargs)
    return wrapper

# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        role = request.form.get("role")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="Username exists")
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    #if "user_id" not in session:
        #return redirect(url_for("login"))

    search = request.args.get("search")

    conn = get_db()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search:
        query += """ AND (
            LOWER(title) LIKE LOWER(?) OR
            LOWER(location) LIKE LOWER(?) OR
            LOWER(job_type) LIKE LOWER(?) OR
            LOWER(experience) LIKE LOWER(?)
        )"""
        params = [f"%{search}%"] * 4

    jobs = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("index.html", jobs=jobs)


# ---------------- ADD JOB ---------------- #

@app.route("/add", methods=["GET", "POST"])
@recruiter_required
def add_job():

    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO jobs
            (title, company, location, skills, experience,
             salary, job_type, description, contact, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("title"),
            request.form.get("company"),
            request.form.get("location"),
            request.form.get("skills"),
            request.form.get("experience"),
            request.form.get("salary"),
            request.form.get("job_type"),
            request.form.get("description"),
            request.form.get("contact"),
            session["user_id"]
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("add_job.html")


# ---------------- VIEW JOB ---------------- #

@app.route("/job/<int:job_id>")
def view_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?", (job_id,)
    ).fetchone()
    conn.close()

    if not job:
        return abort(404)

    return render_template("job_details.html", job=job)


# ---------------- DELETE JOB ---------------- #

@app.route("/delete/<int:job_id>")
@recruiter_required
def delete_job(job_id):

    conn = get_db()
    conn.execute(
        "DELETE FROM jobs WHERE id=? AND user_id=?",
        (job_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("home"))

# ---------------- EDIT JOB ---------------- #

@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
@recruiter_required
def edit_job(job_id):

    conn = get_db()

    # Fetch job owned by logged-in recruiter
    job = conn.execute(
        "SELECT * FROM jobs WHERE id=? AND user_id=?",
        (job_id, session["user_id"])
    ).fetchone()

    if not job:
        conn.close()
        return abort(403)

    if request.method == "POST":

        title = request.form.get("title", "")
        company = request.form.get("company", "")
        location = request.form.get("location", "")
        skills = request.form.get("skills", "")
        experience = request.form.get("experience", "")
        salary = request.form.get("salary", "")
        job_type = request.form.get("job_type", "")
        description = request.form.get("description", "")
        contact = request.form.get("contact", "")

        conn.execute("""
            UPDATE jobs SET
                title=?,
                company=?,
                location=?,
                skills=?,
                experience=?,
                salary=?,
                job_type=?,
                description=?,
                contact=?
            WHERE id=? AND user_id=?
        """, (
            title,
            company,
            location,
            skills,
            experience,
            salary,
            job_type,
            description,
            contact,
            job_id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    conn.close()
    return render_template("edit_job.html", job=job)



# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

=======
from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret123")


# ---------------- DATABASE HELPER ---------------- #

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DATABASE ---------------- #

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        skills TEXT,
        experience TEXT,
        salary TEXT,
        job_type TEXT,
        description TEXT,
        contact TEXT,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


init_db()

@app.route('/google069cb765d388000f.html')
def google_verification():
    return app.send_static_file('google069cb765d388000f.html')

@app.route("/sitemap.xml", methods=["GET"])
def sitemap():

    pages = []

    # static pages
    pages.append(url_for('home', _external=True))
    pages.append(url_for('login', _external=True))
    pages.append(url_for('register', _external=True))

    conn = get_db()
    jobs = conn.execute("SELECT id FROM jobs").fetchall()
    conn.close()

    # dynamic job pages
    for job in jobs:
        pages.append(url_for('view_job', job_id=job["id"], _external=True))

    sitemap_xml = render_template("sitemap.xml", pages=pages)

    response = app.response_class(
        sitemap_xml,
        mimetype='application/xml'
    )

    return response

# ---------------- ROLE DECORATOR ---------------- #

def recruiter_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "recruiter":
            return abort(403)
        return f(*args, **kwargs)
    return wrapper

# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        role = request.form.get("role")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="Username exists")
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search")

    conn = get_db()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search:
        query += """ AND (
            LOWER(title) LIKE LOWER(?) OR
            LOWER(location) LIKE LOWER(?) OR
            LOWER(job_type) LIKE LOWER(?) OR
            LOWER(experience) LIKE LOWER(?)
        )"""
        params = [f"%{search}%"] * 4

    jobs = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("index.html", jobs=jobs)


# ---------------- ADD JOB ---------------- #

@app.route("/add", methods=["GET", "POST"])
@recruiter_required
def add_job():

    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO jobs
            (title, company, location, skills, experience,
             salary, job_type, description, contact, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("title"),
            request.form.get("company"),
            request.form.get("location"),
            request.form.get("skills"),
            request.form.get("experience"),
            request.form.get("salary"),
            request.form.get("job_type"),
            request.form.get("description"),
            request.form.get("contact"),
            session["user_id"]
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("add_job.html")


# ---------------- VIEW JOB ---------------- #

@app.route("/job/<int:job_id>")
def view_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?", (job_id,)
    ).fetchone()
    conn.close()

    if not job:
        return abort(404)

    return render_template("job_details.html", job=job)


# ---------------- DELETE JOB ---------------- #

@app.route("/delete/<int:job_id>")
@recruiter_required
def delete_job(job_id):

    conn = get_db()
    conn.execute(
        "DELETE FROM jobs WHERE id=? AND user_id=?",
        (job_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("home"))

# ---------------- EDIT JOB ---------------- #

@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
@recruiter_required
def edit_job(job_id):

    conn = get_db()

    # Fetch job owned by logged-in recruiter
    job = conn.execute(
        "SELECT * FROM jobs WHERE id=? AND user_id=?",
        (job_id, session["user_id"])
    ).fetchone()

    if not job:
        conn.close()
        return abort(403)

    if request.method == "POST":

        title = request.form.get("title", "")
        company = request.form.get("company", "")
        location = request.form.get("location", "")
        skills = request.form.get("skills", "")
        experience = request.form.get("experience", "")
        salary = request.form.get("salary", "")
        job_type = request.form.get("job_type", "")
        description = request.form.get("description", "")
        contact = request.form.get("contact", "")

        conn.execute("""
            UPDATE jobs SET
                title=?,
                company=?,
                location=?,
                skills=?,
                experience=?,
                salary=?,
                job_type=?,
                description=?,
                contact=?
            WHERE id=? AND user_id=?
        """, (
            title,
            company,
            location,
            skills,
            experience,
            salary,
            job_type,
            description,
            contact,
            job_id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    conn.close()
    return render_template("edit_job.html", job=job)



# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


>>>>>>> c31fe22 (upgrade sitemap)
