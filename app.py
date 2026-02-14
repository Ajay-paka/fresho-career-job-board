from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret123")


# ---------------- DATABASE CONNECTION ---------------- #

def get_db():
    return psycopg2.connect(os.environ.get("AJJU_DATABASE_URL"))


# ---------------- INIT DATABASE ---------------- #

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        skills TEXT,
        experience TEXT,
        salary TEXT,
        job_type TEXT,
        description TEXT,
        contact TEXT,
        user_id INTEGER REFERENCES users(id)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()


# ---------------- GOOGLE VERIFICATION ---------------- #

@app.route('/google069cb765d388000f.html')
def google_verification():
    return app.send_static_file('google069cb765d388000f.html')


# ---------------- SITEMAP ---------------- #

@app.route("/sitemap.xml", methods=["GET"])
def sitemap():

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM jobs")
    jobs = cur.fetchall()
    cur.close()
    conn.close()

    urls = ["https://fresho-career.onrender.com/"]

    for job in jobs:
        urls.append(f"https://fresho-career.onrender.com/job/{job[0]}")

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
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["role"] = user[3]
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
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template("register.html", error="Username already exists")

        cur.close()
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- HOME (PUBLIC) ---------------- #

@app.route("/")
def home():

    search = request.args.get("search")

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM jobs"
    params = []

    if search:
        query += """ WHERE 
            LOWER(title) LIKE LOWER(%s) OR
            LOWER(location) LIKE LOWER(%s) OR
            LOWER(job_type) LIKE LOWER(%s) OR
            LOWER(experience) LIKE LOWER(%s)
        """
        params = [f"%{search}%"] * 4

    cur.execute(query, params)
    jobs = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", jobs=jobs)


# ---------------- ADD JOB ---------------- #

@app.route("/add", methods=["GET", "POST"])
@recruiter_required
def add_job():

    if request.method == "POST":

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO jobs
            (title, company, location, skills, experience,
             salary, job_type, description, contact, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        cur.close()
        conn.close()

        return redirect(url_for("home"))

    return render_template("add_job.html")


# ---------------- VIEW JOB ---------------- #

@app.route("/job/<int:job_id>")
def view_job(job_id):

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id=%s", (job_id,))
    job = cur.fetchone()
    cur.close()
    conn.close()

    if not job:
        return abort(404)

    return render_template("job_details.html", job=job)


# ---------------- DELETE JOB ---------------- #

@app.route("/delete/<int:job_id>")
@recruiter_required
def delete_job(job_id):

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM jobs WHERE id=%s AND user_id=%s",
        (job_id, session["user_id"])
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("home"))


# ---------------- EDIT JOB ---------------- #

@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
@recruiter_required
def edit_job(job_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM jobs WHERE id=%s AND user_id=%s",
        (job_id, session["user_id"])
    )
    job = cur.fetchone()

    if not job:
        cur.close()
        conn.close()
        return abort(403)

    if request.method == "POST":

        cur.execute("""
            UPDATE jobs SET
                title=%s,
                company=%s,
                location=%s,
                skills=%s,
                experience=%s,
                salary=%s,
                job_type=%s,
                description=%s,
                contact=%s
            WHERE id=%s AND user_id=%s
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
            job_id,
            session["user_id"]
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("home"))

    cur.close()
    conn.close()
    return render_template("edit_job.html", job=job)


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
