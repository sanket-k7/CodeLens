# CodeLens

Codebase Intelligence & Developer Onboarding System.

## Current pipeline

GitHub URL -> FastAPI -> Git clone -> file scanner -> source analyzer -> React dashboard

## Features

- Public GitHub repository analysis
- File and language detection
- Python AST analysis for classes, functions, imports and complexity
- JavaScript/TypeScript source analysis
- HTML/CSS analysis
- Technology stack detection
- Developer onboarding starting points
- Search/filter repository files
- Interactive file details
- Functions, classes and dependency views
- FastAPI health endpoint
- Clear API errors for invalid repositories

## Run locally

### Backend

From the CodeLens root:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, normally http://localhost:5173.

## Important

Do not zip `.venv` or `frontend/node_modules`. They are machine-specific and make the project unnecessarily large.

## Roadmap

1. Dependency/architecture graph
2. PostgreSQL analysis history
3. GitHub commit/contributor insights
4. Code quality and security signals
5. Ollama/Qwen onboarding assistant
6. Docker and GitHub Actions
7. Cloud deployment
