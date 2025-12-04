# 🚀 Deployment Guide

This guide explains how to deploy the Indian Equities Analysis Agent to the cloud.

## Option 1: Render (Easiest & Free Tier Available)

Render is great because it supports Docker and has a free tier for web services.

### 1. Push Code to GitHub
Make sure your code is pushed to a GitHub repository.

### 2. Deploy Backend
1. Create a new **Web Service** on Render.
2. Connect your GitHub repo.
3. Settings:
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Environment Variables**:
     - `GEMINI_API_KEY`: Your Gemini API Key
     - `ANTHROPIC_API_KEY`: Your Anthropic API Key (Optional)
4. Click **Create Web Service**.
5. Copy the URL (e.g., `https://my-backend.onrender.com`).

### 3. Deploy Frontend
1. Create another **Web Service** on Render.
2. Connect the same GitHub repo.
3. Settings:
   - **Root Directory**: `frontend`
   - **Runtime**: Docker
   - **Environment Variables**:
     - `BACKEND_URL`: The URL from step 2 (e.g., `https://my-backend.onrender.com`)
4. Click **Create Web Service**.

🎉 Your app is live!

---

## Option 2: Google Cloud Run (Scalable & Serverless)

Perfect for a Google-themed agent!

### Prerequisites
- Google Cloud CLI (`gcloud`) installed
- A Google Cloud Project

### 1. Deploy Backend
```bash
cd backend
gcloud run deploy equities-backend \
  --source . \
  --port 8000 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key_here
```
Copy the Service URL (e.g., `https://equities-backend-xyz.a.run.app`).

### 2. Deploy Frontend
```bash
cd frontend
gcloud run deploy equities-frontend \
  --source . \
  --port 8501 \
  --allow-unauthenticated \
  --set-env-vars BACKEND_URL=https://equities-backend-xyz.a.run.app
```

---

## Option 3: Docker Compose (VPS / Local)

If you have a VPS (like DigitalOcean or EC2) with Docker installed:

1. Copy the project to the server.
2. Set your environment variables:
   ```bash
   export GEMINI_API_KEY="your_key"
   ```
3. Run:
   ```bash
   docker-compose up -d --build
   ```
4. Access at `http://your-server-ip:8501`.
