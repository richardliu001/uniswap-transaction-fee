from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

# Base schema for a transaction
class TransactionBase(BaseModel):
    tx_hash: str
    block_number: int
    time_stamp: datetime
    from_address: str
    to_address: str
    gas: int
    gas_price: int
    gas_used: int
    fee_eth: Decimal
    fee_usdt: Decimal

# Schema for creating a transaction record
class TransactionCreate(TransactionBase):
    pass

# Schema for returning a transaction record
class Transaction(TransactionBase):
    id: int

    class Config:
        orm_mode = True

# Schema for returning summary information
class Summary(BaseModel):
    total_fee_eth: Decimal
    total_fee_usdt: Decimal
    current_eth_price: Decimal
