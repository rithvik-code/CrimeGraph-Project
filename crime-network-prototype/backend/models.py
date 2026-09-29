"""Pydantic models for CrimeGraph AI API."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CaseCreate(BaseModel):
    case_id: str
    title: str
    status: str = "under_investigation"


class CaseResponse(BaseModel):
    id: str
    case_id: str
    title: str
    status: str
    created_at: Optional[str] = None


class EntityBase(BaseModel):
    name: str
    entity_type: str  # person, vehicle, location, phone, financial
    metadata: dict = {}
    confidence: float = 1.0


class EntityResponse(EntityBase):
    id: str
    source_case_id: Optional[str] = None


class RelationBase(BaseModel):
    source_name: str
    target_name: str
    relation_type: str
    priority: str = "supporting"
    confidence: float = 0.5
    evidence: list = []
    case_id: Optional[str] = None


class RelationResponse(RelationBase):
    id: str


class ExtractionRequest(BaseModel):
    text: str = ""
    source_name: str = "manual"


class ExtractionResponse(BaseModel):
    extraction_id: str
    entities: dict
    relations: list
    anomalies: list
    stats: dict


class GraphStats(BaseModel):
    total_cases: int = 0
    persons_identified: int = 0
    vehicles_tracked: int = 0
    locations_mapped: int = 0
    phones_traced: int = 0
    financial_links: int = 0
    emails_found: int = 0
    dates_extracted: int = 0
    ip_addresses_found: int = 0
    addresses_found: int = 0
    total_entities: int = 0
    total_relations: int = 0
    high_risk_connections: int = 0


class AnomalyResponse(BaseModel):
    id: str
    anomaly_type: str
    description: str
    entities_involved: list
    severity: str
    detected_at: str


class UploadResponse(BaseModel):
    success: bool
    results: list = []
    stats: dict = {}
    message: str = ""
