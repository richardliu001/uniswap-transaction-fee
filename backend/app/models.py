from sqlalchemy import Column, Integer, BigInteger, String, DateTime, DECIMAL, TIMESTAMP
from .database import Base

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=False)
    time_stamp = Column(DateTime, nullable=False)
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42), nullable=False)
    gas = Column(BigInteger, nullable=False)
    gas_price = Column(BigInteger, nullable=False)
    gas_used = Column(BigInteger, nullable=False)
    fee_eth = Column(DECIMAL(30, 18), nullable=False)
    fee_usdt = Column(DECIMAL(30, 18), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=False)
    # New column to store the executed swap price decoded from the Uniswap Swap event
    swap_price = Column(DECIMAL(30, 18), nullable=True)
