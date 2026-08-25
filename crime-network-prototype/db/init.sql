-- CrimeGraph AI — PostgreSQL Schema
-- Stores structured case data, entities, and extraction results

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Cases ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) DEFAULT 'under_investigation',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Entities (Persons, Vehicles, Locations, Phones, Financial) ──
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(32) NOT NULL,  -- person, vehicle, location, phone, financial
    metadata JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0,
    source_case_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, entity_type)
);

-- ── Relations (edges between entities) ───────────────────
CREATE TABLE IF NOT EXISTS relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(64) NOT NULL,
    priority VARCHAR(16) DEFAULT 'supporting',  -- supporting, high
    confidence FLOAT DEFAULT 0.5,
    evidence JSONB DEFAULT '[]',
    case_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Extraction Logs ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(32) NOT NULL,  -- text, file, json, csv
    source_name VARCHAR(255),
    raw_text TEXT,
    entities_found JSONB DEFAULT '{}',
    relations_found JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Anomalies ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_type VARCHAR(64) NOT NULL,
    description TEXT,
    entities_involved JSONB DEFAULT '[]',
    severity VARCHAR(16) DEFAULT 'medium',
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_relations_type ON relations(relation_type);
CREATE INDEX idx_relations_priority ON relations(priority);
CREATE INDEX idx_cases_status ON cases(status);
