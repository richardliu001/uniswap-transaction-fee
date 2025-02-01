from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

# Create a new transaction record in the database
def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(
        tx_hash=transaction.tx_hash,
        block_number=transaction.block_number,
        time_stamp=transaction.time_stamp,
        from_address=transaction.from_address,
        to_address=transaction.to_address,
        gas=transaction.gas,
        gas_price=transaction.gas_price,
        gas_used=transaction.gas_used,
        fee_eth=transaction.fee_eth,
        fee_usdt=transaction.fee_usdt,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# Retrieve a transaction record by its hash
def get_transaction_by_hash(db: Session, tx_hash: str):
    return db.query(models.Transaction).filter(models.Transaction.tx_hash == tx_hash).first()

# Retrieve transactions with optional filters and pagination
def get_transactions(db: Session, tx_hash: str = None, start_time: datetime = None, end_time: datetime = None, skip: int = 0, limit: int = 50):
    query = db.query(models.Transaction)
    if tx_hash:
        query = query.filter(models.Transaction.tx_hash == tx_hash)
    if start_time:
        query = query.filter(models.Transaction.time_stamp >= start_time)
    if end_time:
        query = query.filter(models.Transaction.time_stamp <= end_time)
    # Order transactions by timestamp descending (latest first)
    transactions = query.order_by(models.Transaction.time_stamp.desc()).offset(skip).limit(limit).all()
    return transactions

# Retrieve summary information: total fee in ETH and USDT
def get_summary(db: Session):
    from sqlalchemy import func
    result = db.query(
        func.coalesce(func.sum(models.Transaction.fee_eth), 0),
        func.coalesce(func.sum(models.Transaction.fee_usdt), 0)
    ).one()
    total_fee_eth = result[0]
    total_fee_usdt = result[1]
    return total_fee_eth, total_fee_usdt
