# Development Environment Setup Guide

This document outlines the correct procedure for setting up the local development environment for the project. The project relies on a consistent, local Python virtual environment rather than global or Anaconda environments to ensure full reproducibility.

## Required Software
- Python 3.9+
- Node.js 18+ (for frontend)
- Docker Desktop (for database and services)
- VS Code or Antigravity IDE

## Local Environment Hardening
We strictly use a local Python virtual environment located at `backend/venv`. 
**Do not use Anaconda environments directly for this project to avoid conflicting dependencies.**

## Python Environment Setup
1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```
2. **Create the virtual environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the environment**:
   - Windows: `.\venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

*Note: The `requirements.txt` file is curated with exact pip dependencies necessary for FastAPI and database integration.*

## Docker Startup (PostgreSQL Container)
If you have a `docker-compose.yml` file for your database:
```bash
docker-compose up -d
```
Verify that the PostgreSQL container is running on the standard port `5432`.

## Backend Startup
With your virtual environment activated and the database running, start the FastAPI application:
```bash
uvicorn app.main:app --reload
```
Alternatively, if not using the activated terminal, you can run it directly:
```bash
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Frontend Startup
1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```
2. **Install node dependencies**:
   ```bash
   npm install
   ```
3. **Run the development server**:
   ```bash
   npm run dev
   ```

## Common Troubleshooting Steps
- **`ModuleNotFoundError` for `uvicorn` or `python-jose`**: You are likely running the global Python interpreter. Ensure you are using the `backend/venv` environment by running `backend\venv\Scripts\python.exe`.
- **Database Connection Refused**: Verify that your Docker container is running and that `.env` is configured with the correct PostgreSQL credentials.
- **VS Code uses the wrong environment**: Open `.vscode/settings.json` and ensure `"python.defaultInterpreterPath"` is set to `"backend/venv/Scripts/python.exe"`. Restart the integrated terminal.
