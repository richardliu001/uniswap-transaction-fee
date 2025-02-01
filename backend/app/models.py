from sqlalchemy import Column, Integer, BigInteger, String, DateTime, DECIMAL, TIMESTAMP
from .database import Base

# SQLAlchemy model for a Uniswap transaction
class Transaction(Base):
    __tablename__ = 'transactions'

    # Primary key column
    id = Column(Integer, primary_key=True, index=True)
    # Transaction hash (unique)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    # Block number when the transaction was confirmed
    block_number = Column(BigInteger, nullable=False)
    # Timestamp when the transaction was confirmed
    time_stamp = Column(DateTime, nullable=False)
    # Sender address
    from_address = Column(String(42), nullable=False)
    # Receiver address
    to_address = Column(String(42), nullable=False)
    # Gas provided for the transaction
    gas = Column(BigInteger, nullable=False)
    # Gas price in Wei
    gas_price = Column(BigInteger, nullable=False)
    # Actual gas used
    gas_used = Column(BigInteger, nullable=False)
    # Transaction fee in ETH (calculated as gas_used * gas_price / 1e18)
    fee_eth = Column(DECIMAL(30, 18), nullable=False)
    # Transaction fee in USDT (fee_eth * ETH price)
    fee_usdt = Column(DECIMAL(30, 18), nullable=False)
    # Record creation timestamp
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=False)
