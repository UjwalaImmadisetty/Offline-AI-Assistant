# Offline AI Assistant

This is a FastAPI project that lets you upload documents, index them with FAISS, and ask questions using the Ollama AI model.

## Run locally

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the app:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open in browser:

```text
http://127.0.0.1:8000
```

## Deploy to a service

### Option 1: Render

1. Push this repo to GitHub.
2. Create a new Web Service on Render.
3. Connect your GitHub repo.
4. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host=0.0.0.0 --port=$PORT`

### Option 2: Heroku

1. Install the Heroku CLI.
2. Log in: `heroku login`
3. Create app: `heroku create`
4. Push:
   ```powershell
git push heroku main
```

Heroku will use `Procfile` to start the app.

## Important Notes

- `faiss_index/` and `uploads/` are ignored by `.gitignore` because they are generated during runtime.
- Ollama needs to be available to the app. If you use Ollama locally, the deployed version will need access to the same Ollama model or API.
- GitHub only stores your code. To see the running app, you must deploy it to a hosting service.
