# 🔗 CrimeGraph AI — Criminal Network Analysis Platform

> AI-powered platform for analyzing criminal networks through interactive graph visualization, entity extraction, and anomaly detection.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│  React.js  │  Cytoscape.js  │  Recharts  │  CSS (Dark Theme)   │
│  Port: 3000 (Nginx)                                            │
├─────────────────────────────────────────────────────────────────┤
│                        BACKEND                                  │
│  FastAPI  │  spaCy NER  │  Entity Resolution  │  Anomaly Det.  │
│  Port: 8000                                                     │
├──────────────────────┬──────────────────────────────────────────┤
│    PostgreSQL 16     │           Neo4j 5 + GDS                  │
│    Port: 5432        │           Port: 7474/7687                │
│    Structured Data   │           Graph Storage + Analysis       │
└──────────────────────┴──────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React.js + Vite | SPA with component-based architecture |
| **Visualization** | Cytoscape.js | Interactive network graph rendering |
| **Charts** | Recharts | Analytics dashboards and metrics |
| **Styling** | Custom CSS (Dark Theme) | Professional UI design |
| **Backend** | Python + FastAPI | Async REST API with auto-docs |
| **NLP/NER** | spaCy (en_core_web_sm) | Named entity recognition |
| **Entity Resolution** | Custom similarity matching | Deduplication and merging |
| **Anomaly Detection** | NetworkX algorithms | Hub detection, centrality, clusters |
| **Database** | PostgreSQL 16 | Structured case data storage |
| **Graph DB** | Neo4j 5 + GDS | Graph storage and advanced analysis |
| **Graph Analysis** | NetworkX + Neo4j GDS | Path finding, community detection |
| **Deployment** | Docker Compose | Multi-container orchestration |

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Access:
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
# Neo4j:     http://localhost:7474
# PostgreSQL: localhost:5432
```

### Local Development

```bash
# Backend
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
crime-network-prototype/
├── docker-compose.yml          # Multi-service orchestration
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Environment configuration
│   ├── database.py             # PostgreSQL + Neo4j connections
│   ├── models.py               # Pydantic request/response models
│   ├── routes/
│   │   └── api.py              # All API endpoints
│   └── services/
│       ├── ner.py              # spaCy + regex NER
│       ├── entity_resolution.py # Deduplication & merging
│       ├── anomaly.py          # Anomaly detection algorithms
│       └── graph.py            # NetworkX graph builder
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf              # Reverse proxy config
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── main.jsx            # React entry point
│       ├── App.jsx             # Router + layout
│       ├── components/
│       │   ├── Dashboard.jsx   # Stats + case banner
│       │   ├── GraphView.jsx   # Cytoscape.js graph
│       │   ├── CaseReports.jsx # File upload + text input
│       │   └── Analytics.jsx   # Recharts dashboards
│       ├── hooks/
│       │   └── useGraphData.js # Data fetching hook
│       ├── utils/
│       │   └── api.js          # API client
│       └── styles/
│           └── App.css         # Full dark theme
├── db/
│   └── init.sql                # PostgreSQL schema
└── data/
    ├── cases.json              # Operation Shadow Link data
    ├── demo_case_report.txt    # Sample upload file
    ├── sample_upload.json      # Structured JSON sample
    └── sample_upload.csv       # Tabular CSV sample
```

## 🤖 AI/ML Capabilities

### Named Entity Recognition (NER)
- **spaCy** English model for person names, locations, organizations
- **Regex** patterns for phone numbers, vehicles, financial accounts
- Custom stopword filtering to reduce false positives

### Entity Resolution
- **Jaro-Winkler** string similarity for name matching
- Substring detection (e.g., "Pradeep" matches "Pradeep Menon")
- Cluster-based deduplication with confidence scoring

### Anomaly Detection
- **Hub Detection** — Identifies central kingpin figures
- **Financial Chain Analysis** — Circular money flow detection
- **Communication Clustering** — Dense contact network identification
- **Location Convergence** — Multiple suspects at same location
- **Vehicle Sharing** — Coordinated transport patterns
- **Betweenness Centrality** — Bridge node identification

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/graph-data` | Cytoscape.js graph elements |
| GET | `/api/connections` | Edge summary with confidence |
| GET | `/api/anomalies` | Detected anomalies |
| GET | `/api/node/{id}` | Entity details |
| GET | `/api/path?source=&target=` | Shortest path |
| POST | `/api/upload-text` | Extract from pasted text |
| POST | `/api/upload-file` | Extract from uploaded file |
| POST | `/api/load-cases` | Load structured cases |
| POST | `/api/reset` | Reset graph |

## 🎯 Demo Scenario: Operation Shadow Link

**Case ID:** CG-2026-014
**Status:** Under Investigation

Four suspects (Arun Mehta, Rohan Das, Vikram Shah, Karan Patel) connected through:
- 🔴 **High-risk**: Vikram ↔ Karan (80% confidence — shared locations + communication)
- 🟡 **Supporting**: Arun ↔ Rohan (60% — shared storage facility)
- 🟡 **Supporting**: Rohan ↔ Vikram (60% — shared storage facility)

**Upload additional case reports** to expand the graph and discover new connections!

## 📄 License

Built for educational and demonstration purposes.
