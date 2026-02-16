# 🚀 Fresho Career Job Board

A full-stack job board web application built using **Flask + PostgreSQL**.

Live Demo: https://fresho-career.onrender.com/

---

## ✨ Features

- 👤 User Authentication (Login / Register)
- 🔐 Role-Based Access (Recruiter & Candidate)
- 📝 Recruiters can Add / Edit / Delete Jobs
- 🔎 Search & Filter Jobs
- 📄 Job Detail Page
- 📡 Google Sitemap Integration
- 🗄 PostgreSQL Cloud Database (Persistent)
- 🌐 Deployed on Render

---

## 🛠 Tech Stack

- Python (Flask)
- PostgreSQL
- HTML5
- CSS3
- Gunicorn
- Render (Deployment)

---

## 📦 Installation (Local Setup)

```bash
git clone https://github.com/Ajay-paka/fresho-career-job-board.git
cd fresho-career-job-board
pip install -r requirements.txt
python app.py

## 🌍 Environment Variables

Create a `.env` file and add:

DATABASE_URL=your_postgresql_url  
SECRET_KEY=your_secret_key
