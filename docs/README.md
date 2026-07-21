# Finder

Finder is an intelligent tool designed to automate and assist with job applications.

## How to Run

1. **Database**
   ```bash
   cd docker
   docker-compose up -d
   ```

2. **Backend (FastAPI)**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Frontend (React)**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Environment Variables

See `backend/.env.example` for required backend variables.
