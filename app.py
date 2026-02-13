from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ajju"


# ---------------- DATABASE ---------------- #

conn = sqlite3.connect("database.db")
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


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["role"] = user[3]
            return redirect(url_for("home"))
        else:
            return render_template("login.html",
                                   error="Invalid username or password")

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

import sqlite3
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()   #VERY IMPORTANT
            return render_template(
                "register.html",
                error="Username already exists."
            )

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

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search:
        query += " AND (LOWER(title) LIKE LOWER(?) OR LOWER(job_type) LIKE LOWER(?) OR LOWER(location) LIKE LOWER(?)OR LOWER(experience) LIKE LOWER(?))"
        params.append('%' + search + '%')
        params.append('%' + search + '%')
        params.append('%' + search + '%')
        params.append('%' + search + '%')

    c.execute(query, params)
    jobs = c.fetchall()
    conn.close()

    return render_template("index.html", jobs=jobs, request=request)


# ---------------- ADD JOB ---------------- #

@app.route("/add", methods=["GET", "POST"])
def add_job():

    if "user_id" not in session or session["role"] != "recruiter":
        return "Access Denied"
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        skills = request.form["skills"]
        experience = request.form["experience"]
        salary = request.form["salary"]
        job_type = request.form["job_type"]
        description = request.form["description"]
        contact = request.form["contact"]

        c.execute("""INSERT INTO jobs 
            (title, company, location, skills, experience, salary, job_type, description, contact, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, company, location, skills, experience, salary, job_type, description, contact, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    return render_template("add_job.html")


# ---------------- JOB DETAILS ---------------- #

@app.route("/job/<int:job_id>")
def view_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()
    conn.close()

    return render_template("job_details.html", job=job)


# ---------------- DELETE ---------------- #

@app.route("/delete/<int:job_id>")
def delete_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "DELETE FROM jobs WHERE id=? AND user_id=?",
        (job_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for('home'))


# ---------------- EDIT ---------------- #

@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Fetch job first
    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()

    if not job or job[10] != session["user_id"]:
        conn.close()
        return "Access Denied"

    if request.method == "POST":
        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        skills = request.form["skills"]
        experience = request.form["experience"]
        salary = request.form["salary"]
        job_type = request.form["job_type"]
        description = request.form["description"]
        contact = request.form["contact"]

        c.execute("""UPDATE jobs
        SET title=?, company=?, location=?, skills=?, experience=?, salary=?, job_type=?, description=?, contact=? WHERE id=? AND user_id=? """,
        (title, company, location, skills, experience, salary, job_type, description, contact, job_id, session["user_id"]))


        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    conn.close()
    return render_template("edit_job.html", job=job)


# ---------------- RUN ---------------- #
'''
import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))'''

app.run(debug=True)
