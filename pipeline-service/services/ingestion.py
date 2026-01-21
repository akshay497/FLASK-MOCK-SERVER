"""
Data Ingestion Service
Handles fetching data from Flask mock server and upserting into PostgreSQL
"""

import httpx
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from models.customer import Customer

# Flask mock server URL
MOCK_SERVER_URL = "http://mock-server:5000"


async def fetch_all_customers_from_mock_server() -> list:
    """
    Fetch all customers from Flask mock server
    Handles pagination automatically
    """
    all_customers = []
    page = 1
    limit = 100  # Fetch in batches of 100
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            response = await client.get(
                f"{MOCK_SERVER_URL}/api/customers",
                params={"page": page, "limit": limit}
            )
            response.raise_for_status()
            data = response.json()
            
            customers = data.get("data", [])
            all_customers.extend(customers)
            
            # Check if we've fetched all pages
            total = data.get("total", 0)
            if len(all_customers) >= total or len(customers) == 0:
                break
            
            page += 1
    
    return all_customers


def parse_date(date_str: str):
    """Parse date string to date object"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def parse_datetime(datetime_str: str):
    """Parse datetime string to datetime object"""
    if not datetime_str:
        return None
    try:
        # Handle ISO format with T separator
        if "T" in datetime_str:
            return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def upsert_customers(db: Session, customers: list) -> int:
    """
    Upsert customers into PostgreSQL
    Uses PostgreSQL's INSERT ... ON CONFLICT for efficient upsert
    Returns number of records processed
    """
    if not customers:
        return 0
    
    records_processed = 0
    
    for customer_data in customers:
        # Prepare the data
        values = {
            "customer_id": customer_data["customer_id"],
            "first_name": customer_data["first_name"],
            "last_name": customer_data["last_name"],
            "email": customer_data["email"],
            "phone": customer_data.get("phone"),
            "address": customer_data.get("address"),
            "date_of_birth": parse_date(customer_data.get("date_of_birth")),
            "account_balance": Decimal(str(customer_data.get("account_balance", 0))) if customer_data.get("account_balance") is not None else None,
            "created_at": parse_datetime(customer_data.get("created_at"))
        }
        
        # Create upsert statement
        stmt = insert(Customer).values(**values)
        
        # On conflict, update all fields except customer_id
        update_dict = {k: v for k, v in values.items() if k != "customer_id"}
        stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id"],
            set_=update_dict
        )
        
        db.execute(stmt)
        records_processed += 1
    
    db.commit()
    return records_processed
