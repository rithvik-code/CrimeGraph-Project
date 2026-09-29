"""
PostgreSQL Service — Persistent storage for entities, relations, and cases.

Handles CRUD operations against the PostgreSQL database.
Syncs with the in-memory NetworkX graph on startup.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import AsyncSessionLocal


async def init_db():
    """Create tables if they don't exist (safety net)."""
    async with AsyncSessionLocal() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS cases (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                case_id VARCHAR(64) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                status VARCHAR(32) DEFAULT 'under_investigation',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """))
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS entities (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL,
                entity_type VARCHAR(32) NOT NULL,
                metadata JSONB DEFAULT '{}',
                confidence FLOAT DEFAULT 1.0,
                source_case_id VARCHAR(64),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(name, entity_type)
            );
        """))
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS relations (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                source_name VARCHAR(255) NOT NULL,
                target_name VARCHAR(255) NOT NULL,
                source_entity_id UUID,
                target_entity_id UUID,
                relation_type VARCHAR(64) NOT NULL,
                priority VARCHAR(16) DEFAULT 'supporting',
                confidence FLOAT DEFAULT 0.5,
                evidence JSONB DEFAULT '[]',
                case_id VARCHAR(64),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """))
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS extractions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                source_type VARCHAR(32) NOT NULL,
                source_name VARCHAR(255),
                raw_text TEXT,
                entities_found JSONB DEFAULT '{}',
                relations_found JSONB DEFAULT '[]',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """))
        # Create indexes if not exist
        await session.execute(text("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS idx_relations_priority ON relations(priority)"))
        await session.commit()


# ── Entity CRUD ─────────────────────────────────────────

async def upsert_entity(session: AsyncSession, name: str, entity_type: str,
                         metadata: dict = None, confidence: float = 1.0,
                         source_case_id: str = None) -> str:
    """Insert or update an entity. Returns the entity ID."""
    result = await session.execute(
        text("SELECT id FROM entities WHERE name = :name AND entity_type = :type"),
        {"name": name, "type": entity_type}
    )
    row = result.fetchone()
    if row:
        return str(row[0])

    entity_id = str(uuid.uuid4())
    await session.execute(
        text("""INSERT INTO entities (id, name, entity_type, metadata, confidence, source_case_id)
                VALUES (:id, :name, :type, :metadata, :confidence, :source)
                ON CONFLICT (name, entity_type) DO UPDATE SET
                    metadata = entities.metadata || :metadata,
                    confidence = GREATEST(entities.confidence, :confidence)"""),
        {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "metadata": json.dumps(metadata or {}),
            "confidence": confidence,
            "source": source_case_id,
        }
    )
    return entity_id


async def upsert_entities_batch(session: AsyncSession, entities: dict, source_label: str = "") -> dict:
    """Batch upsert all entities from extraction. Returns name -> id mapping."""
    name_to_id = {}

    for name in entities.get("people", []):
        eid = await upsert_entity(session, name, "person", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("phones", []):
        eid = await upsert_entity(session, name, "phone", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("locations", []):
        eid = await upsert_entity(session, name, "location", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("vehicles", []):
        eid = await upsert_entity(session, name, "vehicle", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("financial", []):
        eid = await upsert_entity(session, name, "financial", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("emails", []):
        eid = await upsert_entity(session, name, "email", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("dates", []):
        eid = await upsert_entity(session, name, "date", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("ip_addresses", []):
        eid = await upsert_entity(session, name, "ip_address", source_case_id=source_label)
        name_to_id[name] = eid
    for name in entities.get("addresses", []):
        eid = await upsert_entity(session, name, "address", source_case_id=source_label)
        name_to_id[name] = eid

    return name_to_id


# ── Relation CRUD ───────────────────────────────────────

async def upsert_relation(session: AsyncSession, source_name: str, target_name: str,
                           relation_type: str, priority: str = "supporting",
                           confidence: float = 0.5, evidence: list = None,
                           case_id: str = None) -> Optional[str]:
    """Insert or update a relation. Returns the relation ID."""
    # Check if relation already exists
    result = await session.execute(
        text("""SELECT id FROM relations
                WHERE source_name = :src AND target_name = :tgt AND relation_type = :rtype"""),
        {"src": source_name, "tgt": target_name, "rtype": relation_type}
    )
    row = result.fetchone()
    if row:
        # Update confidence and priority
        await session.execute(
            text("""UPDATE relations SET
                    confidence = GREATEST(confidence, :conf),
                    priority = CASE WHEN :priority = 'high' THEN 'high' ELSE priority END
                    WHERE id = :id"""),
            {"conf": confidence, "priority": priority, "id": row[0]}
        )
        return str(row[0])

    rel_id = str(uuid.uuid4())
    await session.execute(
        text("""INSERT INTO relations (id, source_name, target_name, relation_type,
                priority, confidence, evidence, case_id)
                VALUES (:id, :src, :tgt, :rtype, :priority, :conf, :evidence, :case)"""),
        {
            "id": rel_id,
            "src": source_name,
            "tgt": target_name,
            "rtype": relation_type,
            "priority": priority,
            "conf": confidence,
            "evidence": json.dumps(evidence or []),
            "case": case_id,
        }
    )
    return rel_id


async def upsert_relations_batch(session: AsyncSession, relations: list, source_label: str = "") -> int:
    """Batch upsert relations. Returns count of relations upserted."""
    count = 0
    for rel in relations:
        src = rel.get("source", "")
        tgt = rel.get("target", "")
        if src and tgt:
            await upsert_relation(
                session, src, tgt,
                rel.get("relation_type", "linked"),
                rel.get("priority", "supporting"),
                confidence=0.7 if rel.get("priority") == "high" else 0.5,
                evidence=[rel.get("evidence", "")],
                case_id=source_label,
            )
            count += 1
    return count


# ── Co-occurrence Links ─────────────────────────────────

async def add_cooccurrence_links(session: AsyncSession, entities: dict, source_label: str = "") -> int:
    """Add co-occurrence links between people and their associated entities."""
    count = 0
    for p in entities.get("people", []):
        for loc in entities.get("locations", []):
            await upsert_relation(session, p, loc, "located_at", case_id=source_label)
            count += 1
        for ph in entities.get("phones", []):
            await upsert_relation(session, p, ph, "has_phone", case_id=source_label)
            count += 1
        for v in entities.get("vehicles", []):
            await upsert_relation(session, p, v, "associated_vehicle", case_id=source_label)
            count += 1
        for fin in entities.get("financial", []):
            await upsert_relation(session, p, fin, "associated_financial", case_id=source_label)
            count += 1
        for em in entities.get("emails", []):
            await upsert_relation(session, p, em, "has_email", case_id=source_label)
            count += 1
        for ip in entities.get("ip_addresses", []):
            await upsert_relation(session, p, ip, "associated_ip", case_id=source_label)
            count += 1
        for addr in entities.get("addresses", []):
            await upsert_relation(session, p, addr, "associated_address", case_id=source_label)
            count += 1

    # Link dates to people and locations
    for dt in entities.get("dates", []):
        for p in entities.get("people", []):
            await upsert_relation(session, p, dt, "occurred_on", case_id=source_label)
            count += 1
        for loc in entities.get("locations", []):
            await upsert_relation(session, loc, dt, "incident_date", case_id=source_label)
            count += 1

    return count


# ── Load All Data ───────────────────────────────────────

async def load_all_entities(session: AsyncSession) -> list[dict]:
    """Load all entities from PostgreSQL."""
    result = await session.execute(
        text("SELECT name, entity_type, confidence FROM entities ORDER BY entity_type, name")
    )
    return [{"name": r[0], "type": r[1], "confidence": r[2]} for r in result.fetchall()]


async def load_all_relations(session: AsyncSession) -> list[dict]:
    """Load all relations from PostgreSQL."""
    result = await session.execute(
        text("SELECT source_name, target_name, relation_type, priority, confidence FROM relations")
    )
    return [{"source": r[0], "target": r[1], "relation_type": r[2],
             "priority": r[3], "confidence": r[4]} for r in result.fetchall()]


# ── Stats ───────────────────────────────────────────────

async def get_db_stats(session: AsyncSession) -> dict:
    """Get entity counts by type from PostgreSQL."""
    result = await session.execute(
        text("SELECT entity_type, count(*) FROM entities GROUP BY entity_type")
    )
    type_counts = {r[0]: r[1] for r in result.fetchall()}

    rel_result = await session.execute(text("SELECT count(*) FROM relations"))
    total_relations = rel_result.fetchone()[0]

    high_result = await session.execute(
        text("SELECT count(*) FROM relations WHERE priority = 'high'")
    )
    high_risk = high_result.fetchone()[0]

    return {
        "persons_identified": type_counts.get("person", 0),
        "vehicles_tracked": type_counts.get("vehicle", 0),
        "locations_mapped": type_counts.get("location", 0),
        "phones_traced": type_counts.get("phone", 0),
        "financial_links": type_counts.get("financial", 0),
        "emails_found": type_counts.get("email", 0),
        "dates_extracted": type_counts.get("date", 0),
        "ip_addresses_found": type_counts.get("ip_address", 0),
        "addresses_found": type_counts.get("address", 0),
        "total_entities": sum(type_counts.values()),
        "total_relations": total_relations,
        "connections": total_relations,
        "high_risk_connections": high_risk,
    }


async def reset_db(session: AsyncSession):
    """Clear all data from PostgreSQL."""
    await session.execute(text("DELETE FROM relations"))
    await session.execute(text("DELETE FROM entities"))
    await session.execute(text("DELETE FROM extractions"))
    await session.commit()
