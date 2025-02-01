from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

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
    created_at: datetime
    swap_price: Optional[Decimal] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int

    class Config:
        orm_mode = True

class Summary(BaseModel):
    total_fee_eth: Decimal
    total_fee_usdt: Decimal
    current_eth_price: Decimal

# New schema for returning the swap price response
class SwapPriceResponse(BaseModel):
    tx_hash: str
    swap_price: Decimal
