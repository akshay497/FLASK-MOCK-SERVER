# Customer Data Pipeline

A data pipeline with 3 Docker services that demonstrates data flow from a mock server through an ingestion service into PostgreSQL.

## Architecture

```
Flask (JSON) → FastAPI (Ingest) → PostgreSQL → API Response
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| **PostgreSQL** | 5432 | Data storage for customer records |
| **Mock Server (Flask)** | 5000 | REST API serving customer data from JSON file |
| **Pipeline Service (FastAPI)** | 8000 | Data ingestion pipeline with database endpoints |

## Prerequisites

- Docker Desktop (running)
- Python 3.10+ (for local development)
- Git

### Verify Docker is working

```bash
docker --version
docker-compose --version
```

## Quick Start

### 1. Clone and navigate to project

```bash
cd backend-assessment
```

### 2. Start all services

```bash
docker-compose up -d
```

### 3. Wait for services to be ready (approximately 30 seconds)

```bash
docker-compose ps
```

All services should show "healthy" or "running" status.

### 4. Test the pipeline

```bash
# Test Flask Mock Server health
curl http://localhost:5000/api/health

# Get customers from Mock Server (paginated)
curl "http://localhost:5000/api/customers?page=1&limit=5"

# Get single customer from Mock Server
curl http://localhost:5000/api/customers/CUST001

# Ingest data into PostgreSQL
curl -X POST http://localhost:8000/api/ingest

# Get customers from Pipeline Service (from database)
curl "http://localhost:8000/api/customers?page=1&limit=5"

# Get single customer from Pipeline Service
curl http://localhost:8000/api/customers/CUST001
```

## API Endpoints

### Mock Server (Flask) - Port 5000

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/customers` | GET | Paginated customer list |
| `/api/customers/{id}` | GET | Single customer by ID |

**Query Parameters for `/api/customers`:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 10, max: 100)

**Response Format:**
```json
{
  "data": [...],
  "total": 25,
  "page": 1,
  "limit": 10,
  "total_pages": 3
}
```

### Pipeline Service (FastAPI) - Port 8000

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/ingest` | POST | Ingest data from Mock Server into PostgreSQL |
| `/api/customers` | GET | Paginated customer list from database |
| `/api/customers/{id}` | GET | Single customer by ID from database |

**Ingest Response:**
```json
{
  "status": "success",
  "records_processed": 25
}
```

## Project Structure

```
FLASK-MOCK-SERVER/
├── docker-compose.yml
├── README.md
├── mock-server/
│   ├── app.py                 # Flask application
│   ├── data/
│   │   └── customers.json     # Customer data (25 records)
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-service/
    ├── main.py                # FastAPI application
    ├── database.py            # SQLAlchemy configuration
    ├── models/
    │   ├── __init__.py
    │   └── customer.py        # Customer SQLAlchemy model
    ├── services/
    │   ├── __init__.py
    │   └── ingestion.py       # Data ingestion logic
    ├── Dockerfile
    └── requirements.txt
```

## Database Schema

**Table: `customers`**

| Column | Type | Constraints |
|--------|------|-------------|
| customer_id | VARCHAR(50) | PRIMARY KEY |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(20) | NULLABLE |
| address | TEXT | NULLABLE |
| date_of_birth | DATE | NULLABLE |
| account_balance | DECIMAL(15,2) | NULLABLE |
| created_at | TIMESTAMP | NULLABLE |

## Features

### Mock Server (Flask)
- ✅ Loads customer data from JSON file (not hardcoded)
- ✅ Pagination support with page and limit parameters
- ✅ 404 response for missing customers
- ✅ Health check endpoint

### Pipeline Service (FastAPI)
- ✅ SQLAlchemy ORM model for customers
- ✅ Auto-pagination when fetching from Flask
- ✅ Upsert logic (INSERT ... ON CONFLICT DO UPDATE)
- ✅ Comprehensive error handling
- ✅ Database connection pooling

### Docker Compose
- ✅ Health checks for all services
- ✅ Proper dependency ordering
- ✅ Persistent volume for PostgreSQL
- ✅ Environment variable configuration

## Development

### Stopping Services

```bash
docker-compose down
```

### Stopping Services and Removing Data

```bash
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f pipeline-service
```

### Rebuilding After Code Changes

```bash
docker-compose up -d --build
```

## Testing Complete Flow

```bash
# 1. Start services
docker-compose up -d

# 2. Wait for services
sleep 30

# 3. Verify Mock Server
echo "=== Mock Server Health ==="
curl -s http://localhost:5000/api/health | python3 -m json.tool

echo "\n=== Mock Server Customers (Page 1) ==="
curl -s "http://localhost:5000/api/customers?page=1&limit=5" | python3 -m json.tool

# 4. Ingest Data
echo "\n=== Ingesting Data ==="
curl -s -X POST http://localhost:8000/api/ingest | python3 -m json.tool

# 5. Verify Pipeline Service
echo "\n=== Pipeline Service Customers (Page 1) ==="
curl -s "http://localhost:8000/api/customers?page=1&limit=5" | python3 -m json.tool

echo "\n=== Single Customer ==="
curl -s http://localhost:8000/api/customers/CUST001 | python3 -m json.tool
```

## Troubleshooting

### Services not starting
```bash
# Check service status
docker-compose ps

# Check logs for errors
docker-compose logs
```

### Database connection issues
```bash
# Ensure PostgreSQL is healthy
docker-compose exec postgres pg_isready -U postgres
```

### Port conflicts
Ensure ports 5000, 5432, and 8000 are not in use by other applications.

## Environment Variables

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| DATABASE_URL | pipeline-service | postgresql://postgres:password@postgres:5432/customer_db | PostgreSQL connection string |
| POSTGRES_USER | postgres | postgres | Database user |
| POSTGRES_PASSWORD | postgres | password | Database password |
| POSTGRES_DB | postgres | customer_db | Database name |
