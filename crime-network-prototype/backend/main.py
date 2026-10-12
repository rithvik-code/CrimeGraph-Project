"""
CrimeGraph AI — FastAPI Application

Architecture:
  Frontend: React + Cytoscape.js + Recharts
  Backend:  FastAPI + NLP (spaCy) + NetworkX
  Database: PostgreSQL 16 + Neo4j 5 GDS
  Deploy:   Docker Compose
"""

import logging
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.api import router as api_router
from backend.routes.investigator import router as investigator_router
from backend.routes.crime_news import router as crime_news_router
from backend.config import CORS_ORIGINS, APP_ENV, API_KEYS, AUTH_ENABLED, RATE_LIMIT_PER_MINUTE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize databases on startup and load persisted data."""
    # ── Startup ───────────────────────────────────────────
    logger.info("Starting CrimeGraph AI...")

    # 1. Init PostgreSQL tables
    try:
        from backend.services.db_service import init_db
        await init_db()
        logger.info("PostgreSQL tables initialized")
    except Exception as e:
        logger.warning(f"PostgreSQL init failed (will use in-memory only): {e}")

    # 2. Init Neo4j constraints
    try:
        from backend.services.neo4j_service import init_neo4j_constraints
        await init_neo4j_constraints()
        logger.info("Neo4j constraints initialized")
    except Exception as e:
        logger.warning(f"Neo4j init failed (will use in-memory only): {e}")

    # 3. Load persisted data from PostgreSQL into the in-memory graph
    try:
        from backend.services.db_service import load_all_entities, load_all_relations
        from backend.database import AsyncSessionLocal
        from backend.routes.api import graph

        async with AsyncSessionLocal() as session:
            entities = await load_all_entities(session)
            relations = await load_all_relations(session)

            if entities:
                # Rebuild the in-memory graph from PostgreSQL
                from backend.services.graph import CaseGraph
                # Import the global graph module
                import backend.routes.api as api_module

                # Load entities
                for ent in entities:
                    etype = ent["type"]
                    name = ent["name"]
                    if etype == "person":
                        api_module.graph.add_person(name)
                    elif etype == "phone":
                        api_module.graph.add_phone(name)
                    elif etype == "location":
                        api_module.graph.add_location(name)
                    elif etype == "vehicle":
                        api_module.graph.add_vehicle(name)
                    elif etype == "financial":
                        api_module.graph.add_financial(name)
                    elif etype == "email":
                        api_module.graph.add_email(name)
                    elif etype == "date":
                        api_module.graph.add_date(name)
                    elif etype == "ip_address":
                        api_module.graph.add_ip_address(name)
                    elif etype == "address":
                        api_module.graph.add_address(name)

                # Load relations
                for rel in relations:
                    src, tgt = rel["source"], rel["target"]
                    if api_module.graph.g.has_node(src) and api_module.graph.g.has_node(tgt):
                        api_module.graph.link(
                            src, tgt,
                            rel["relation_type"],
                            priority=rel["priority"],
                            confidence=rel["confidence"],
                        )

                logger.info(f"Loaded {len(entities)} entities, {len(relations)} relations from PostgreSQL")

                # 4. Sync to Neo4j in background
                try:
                    from backend.services.neo4j_service import sync_graph_to_neo4j
                    await sync_graph_to_neo4j(api_module.graph)
                    logger.info("Graph synced to Neo4j")
                except Exception as e:
                    logger.warning(f"Neo4j sync failed: {e}")
            else:
                logger.info("No persisted data found — starting fresh")

    except Exception as e:
        logger.warning(f"Failed to load persisted data: {e}")

    logger.info("CrimeGraph AI is ready")
    yield
    # ── Shutdown ──────────────────────────────────────────
    logger.info("Shutting down CrimeGraph AI...")
    try:
        from backend.database import close_neo4j
        await close_neo4j()
    except Exception:
        pass


app = FastAPI(
    title="CrimeGraph AI",
    description="AI-powered criminal network analysis platform",
    version="3.0.0",
    lifespan=lifespan,
)
_request_windows = defaultdict(deque)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach a request ID and consistent timing headers to every response."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request failure", extra={"request_id": request_id})
        response = JSONResponse(status_code=500, content={
            "detail": "Internal server error",
            "request_id": request_id,
        })
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
    return response


@app.middleware("http")
async def api_access_middleware(request: Request, call_next):
    """Optional API-key auth plus a small bounded in-process rate limiter."""
    if request.url.path.startswith("/api"):
        if AUTH_ENABLED and request.headers.get("X-API-Key") not in API_KEYS:
            return JSONResponse(status_code=401, content={"detail": "API authentication required"})

        client = request.client.host if request.client else "unknown"
        bucket = _request_windows[client]
        now = time.monotonic()
        while bucket and now - bucket[0] >= 60:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MINUTE:
            response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            response.headers["Retry-After"] = "60"
            return response
        bucket.append(now)
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if APP_ENV == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

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
app.include_router(investigator_router)
app.include_router(crime_news_router)


@app.get("/")
async def root():
    return {
        "service": "CrimeGraph AI",
        "version": "3.0.0",
        "architecture": {
            "frontend": ["React.js", "Cytoscape.js", "Recharts", "Leaflet"],
            "backend": ["FastAPI", "Python 3.11"],
            "ai_ml": ["spaCy NER", "Entity Resolution", "Anomaly Detection"],
            "database": ["PostgreSQL 16", "Neo4j 5 + GDS"],
            "graph_analysis": ["NetworkX", "Neo4j GDS"],
            "deployment": ["Docker Compose"],
        },
    }


@app.get("/health")
async def health():
    """Health check including database connectivity."""
    status = {"status": "healthy", "databases": {}}

    # Check PostgreSQL
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            status["databases"]["postgresql"] = "connected"
    except Exception:
        status["databases"]["postgresql"] = "unavailable"

    # Check Neo4j
    try:
        from backend.database import get_neo4j
        driver = get_neo4j()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS test")
            await result.single()
            status["databases"]["neo4j"] = "connected"
    except Exception:
        status["databases"]["neo4j"] = "unavailable"

    if any(value != "connected" for value in status["databases"].values()):
        status["status"] = "degraded"

    return status


@app.get("/metrics")
async def metrics():
    """Small JSON operational snapshot suitable for a local monitor."""
    from backend.routes.api import graph
    return {
        "service": app.title,
        "environment": APP_ENV,
        "graph": graph.stats(),
        "rate_limit_clients": len(_request_windows),
        "auth_enabled": AUTH_ENABLED,
    }
