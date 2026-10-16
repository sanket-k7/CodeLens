from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analyzer.github_cloner import analyze_github_repository

app = FastAPI(title='CodeLens API', version='1.0.0', description='Codebase intelligence API for developer onboarding')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://localhost:5174'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class RepositoryRequest(BaseModel):
    github_url: str = Field(min_length=1, max_length=500)

@app.get('/')
def home():
    return {'message': 'Welcome to CodeLens', 'status': 'running', 'docs': '/docs'}

@app.get('/health')
def health():
    return {'status': 'healthy'}

@app.post('/repository/analyze')
def analyze_repository(request: RepositoryRequest):
    try:
        return analyze_github_repository(request.github_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Analysis failed: {exc}')
