"""Pydantic models for CrimeGraph AI API."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import datetime


class CaseCreate(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    status: str = Field(default="under_investigation", min_length=1, max_length=32)


class CaseResponse(BaseModel):
    id: str
    case_id: str
    title: str
    status: str
    created_at: Optional[str] = None


class EntityBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    entity_type: str = Field(min_length=1, max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class EntityResponse(EntityBase):
    id: str
    source_case_id: Optional[str] = None


class RelationBase(BaseModel):
    source_name: str = Field(min_length=1, max_length=255)
    target_name: str = Field(min_length=1, max_length=255)
    relation_type: str = Field(min_length=1, max_length=64)
    priority: str = Field(default="supporting", min_length=1, max_length=16)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: list[Any] = Field(default_factory=list)
    case_id: Optional[str] = Field(default=None, max_length=64)


class RelationResponse(RelationBase):
    id: str


class ExtractionRequest(BaseModel):
    text: str = Field(default="", max_length=1_000_000)
    source_name: str = Field(default="manual", min_length=1, max_length=255)


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
    results: list = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)
    message: str = ""
