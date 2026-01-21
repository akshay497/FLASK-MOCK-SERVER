"""
FastAPI Pipeline Service
Ingests data from Flask mock server into PostgreSQL
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging

from database import get_db, init_db
from models.customer import Customer
from services.ingestion import fetch_all_customers_from_mock_server, upsert_customers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    yield


app = FastAPI(
    title="Customer Pipeline Service",
    description="Data ingestion pipeline for customer data",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pipeline-service"
    }


@app.post("/api/ingest")
async def ingest_data(db: Session = Depends(get_db)):
    """
    Ingest all customer data from Flask mock server into PostgreSQL
    Fetches all pages automatically and performs upsert
    """
    try:
        logger.info("Starting data ingestion from mock server...")
        
        # Fetch all customers from mock server
        customers = await fetch_all_customers_from_mock_server()
        logger.info(f"Fetched {len(customers)} customers from mock server")
        
        # Upsert into PostgreSQL
        records_processed = upsert_customers(db, customers)
        logger.info(f"Successfully processed {records_processed} records")
        
        return {
            "status": "success",
            "records_processed": records_processed
        }
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.get("/api/customers")
def get_customers(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of customers from database
    Query params:
        - page: Page number (default: 1)
        - limit: Items per page (default: 10, max: 100)
    """
    # Get total count
    total = db.query(Customer).count()
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get paginated customers
    customers = db.query(Customer).offset(offset).limit(limit).all()
    
    return {
        "data": [customer.to_dict() for customer in customers],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 0
    }


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """
    Get a single customer by ID
    Returns 404 if customer not found
    """
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer with ID '{customer_id}' not found"
        )
    
    return {
        "data": customer.to_dict()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
