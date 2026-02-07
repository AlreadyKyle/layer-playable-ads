"""FastAPI app for Layer.ai Playable Studio."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import workspace, analyze, generate, build, demo

app = FastAPI(
    title="Layer.ai Playable Studio API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspace.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(build.router, prefix="/api")
app.include_router(demo.router, prefix="/api")


@app.get("/api/health")
def health():
    from src.utils.helpers import validate_api_keys
    return {"status": "ok", "api_keys": validate_api_keys()}
