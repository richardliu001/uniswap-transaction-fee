from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from .. import crud, schemas, tasks
from ..database import SessionLocal

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@router.get("/{tx_hash}", response_model=schemas.Transaction)
def read_transaction(tx_hash: str, db: Session = Depends(get_db)):
    transaction = crud.get_transaction_by_hash(db, tx_hash)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.post("/historical", response_model=dict)
def process_historical_transactions(
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
):
    # Stub implementation for historical processing.
    return {"message": "Historical processing initiated. (Not implemented)"}

@router.get("/swapprice/{tx_hash}", response_model=schemas.SwapPriceResponse)
def get_swap_price(tx_hash: str, db: Session = Depends(get_db)):
    """
    Get the decoded swap price for a transaction.
    If the transaction exists but does not have a swap price, decode it on the fly.
    """
    transaction = crud.get_transaction_by_hash(db, tx_hash)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.swap_price is None:
        swap_price = tasks.decode_swap_price(tx_hash)
        if swap_price == 0:
            raise HTTPException(status_code=400, detail="Swap price could not be decoded")
        transaction = crud.update_swap_price(db, tx_hash, swap_price)
    return schemas.SwapPriceResponse(tx_hash=transaction.tx_hash, swap_price=transaction.swap_price)
