"""Async PostgreSQL and Neo4j connection management."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from neo4j import AsyncGraphDatabase
from backend.config import DATABASE_URL, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# ── PostgreSQL ────────────────────────────────────────────
pg_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"timeout": 10, "command_timeout": 30},
)
AsyncSessionLocal = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """FastAPI dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        yield session

# ── Neo4j ─────────────────────────────────────────────────
neo4j_driver = None

def get_neo4j():
    """Get or create the Neo4j async driver singleton."""
    global neo4j_driver
    if neo4j_driver is None:
        neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return neo4j_driver

async def close_neo4j():
    global neo4j_driver
    if neo4j_driver:
        await neo4j_driver.close()
        neo4j_driver = None

async def neo4j_session():
    """Context manager for a Neo4j session."""
    driver = get_neo4j()
    async with driver.session() as session:
        return session
