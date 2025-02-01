from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint to retrieve a list of transactions with optional filters and pagination
@router.get("/", response_model=List[schemas.Transaction])
def read_transactions(
    tx_hash: Optional[str] = Query(None, description="Transaction hash to filter"),
    start_time: Optional[datetime] = Query(None, description="Start time in ISO format"),
    end_time: Optional[datetime] = Query(None, description="End time in ISO format"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of transactions per page"),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    transactions = crud.get_transactions(db, tx_hash, start_time, end_time, skip, page_size)
    return transactions

# Endpoint to retrieve a single transaction by its hash
@router.get("/{tx_hash}", response_model=schemas.Transaction)
def read_transaction(tx_hash: str, db: Session = Depends(get_db)):
    transaction = crud.get_transaction_by_hash(db, tx_hash)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

# Endpoint to initiate historical transaction processing (batch job)
@router.post("/historical", response_model=dict)
def process_historical_transactions(
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
):
    # This is a stub implementation.
    # In production, implement fetching and processing of historical data.
    return {"message": "Historical processing initiated. (Not implemented)"}
