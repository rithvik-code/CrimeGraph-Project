"""
CrimeGraph AI — FastAPI Application

Architecture:
  Frontend: React + Cytoscape.js + Recharts
  Backend:  FastAPI + NLP (spaCy) + NetworkX
  Database: PostgreSQL + Neo4j GDS
  Deploy:   Docker Compose
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.api import router as api_router
from backend.config import CORS_ORIGINS

app = FastAPI(
    title="CrimeGraph AI",
    description="AI-powered criminal network analysis platform",
    version="2.0.0",
)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "CrimeGraph AI",
        "version": "2.0.0",
        "architecture": {
            "frontend": ["React.js", "Cytoscape.js", "Recharts"],
            "backend": ["FastAPI", "Python 3.11"],
            "ai_ml": ["spaCy NER", "Entity Resolution", "Anomaly Detection"],
            "database": ["PostgreSQL 16", "Neo4j 5 + GDS"],
            "graph_analysis": ["NetworkX", "Neo4j GDS"],
            "deployment": ["Docker Compose"],
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
