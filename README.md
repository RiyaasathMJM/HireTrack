# HireTrack

A modern, lightweight applicant tracking system (ATS) for recruiters sorting through high volumes of applications. Upload resumes, automatically extract key candidate information, filter/search applicants, manage pipeline stages, score candidates against job descriptions, and generate AI-powered summaries.

---

## 🌟 Tech Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind/CSS modules, Lucide icons, Recharts
- **Backend:** Python Flask, Psycopg2, Gunicorn
- **Database:** Supabase (Managed PostgreSQL 17 with connection pooling)
- **Deployment:** 
  - Backend on **Railway**
  - Frontend on **Netlify**
- **AI / Parsing:** OpenAI API (optional, with heuristic rule-based fallback), `pypdf`, `python-docx`

---

## 🚀 Live Deployments

- **Backend API (Railway):** [`https://hiretrack-production-c2db.up.railway.app`](https://hiretrack-production-c2db.up.railway.app)
  - Health check: [`https://hiretrack-production-c2db.up.railway.app/api/health`](https://hiretrack-production-c2db.up.railway.app/api/health)
- **Database (Supabase):** Hosted PostgreSQL 17 instance with IPv4 transaction pooler.
- **Frontend (Netlify):** Connect repo on [Netlify](https://app.netlify.com/signup/start/connect/repos/RiyaasathMJM%2FHireTrack) with automated builds via `netlify.toml`.

---

## ✨ Features

- **Bulk Resume Upload:** Support for `.pdf`, `.docx`, and `.txt` files with concurrent processing.
- **Automated Resume Parsing:** Extracts candidate name, email, phone number, and skills.
- **Smart JD Matching:** Deterministic skill-overlap scoring against saved or ad-hoc job descriptions.
- **AI Candidate Summaries:** One-click candidate summaries with automatic fallback to local heuristic extraction if no OpenAI API key is set.
- **Pipeline Stage Management:** Drag or select candidates across stages: `applied` → `screening` → `interview` → `offer` → `rejected`.
- **Search & Filter:** Instant full-text search across candidate names, skills, and resume contents.
- **Rating & Notes:** Star ratings (1-5) and custom recruiter notes saved in real-time.

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL database (or Supabase connection)

### 2. Backend Setup

```bash
cd Backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `Backend/.env` with your Supabase / PostgreSQL credentials:
```env
PORT=5000
FLASK_DEBUG=true

# Database (Supabase PostgreSQL)
PG_HOST=aws-0-ap-southeast-1.pooler.supabase.com
PG_PORT=6543
PG_USER=postgres.your_project_ref
PG_PASSWORD=your_database_password
PG_DATABASE=postgres
PG_SSLMODE=require

# Optional AI Features
OPENAI_API_KEY=
```

Run the backend server:
```bash
python app.py
```
Backend will start on `http://localhost:5000`.

---

### 3. Frontend Setup

```bash
cd Frontend

# Install dependencies
npm install

# Start local Vite development server
npm run dev
```

Frontend will run locally on `http://localhost:5173`.

---

## 🚢 Production Deployment

### Backend (Railway)
The backend includes a `Dockerfile` and `Procfile`.
- Configure the environment variables in your Railway service:
  - `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`, `PG_SSLMODE`
  - `PORT=5000`
- Railway builds and runs the container automatically.

### Frontend (Netlify)
The root `netlify.toml` handles routing and builds:
- **Base directory:** `Frontend`
- **Build command:** `npm run build`
- **Publish directory:** `dist`
- **Redirects:** `/* -> /index.html 200` (SPA routing)
- Environment variable: `VITE_API_URL=https://hiretrack-production-c2db.up.railway.app`

---

## 📄 License
MIT
