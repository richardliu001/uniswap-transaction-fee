import time
import threading
import requests
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from . import crud, schemas
from .database import SessionLocal
from .config import settings
import logging

# Configure logger for background tasks
logger = logging.getLogger("background_tasks")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# Fetch the current ETH/USDT price from Binance
def fetch_eth_price():
    try:
        response = requests.get(settings.BINANCE_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = Decimal(data.get("price", "0"))
            return price
        else:
            logger.error(f"Failed to fetch ETH price: {response.status_code}")
            return Decimal("0")
    except Exception as e:
        logger.error(f"Exception fetching ETH price: {e}")
        return Decimal("0")


# Fetch live transactions from Etherscan API
def fetch_live_transactions():
    try:
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
            "page": 1,
            "offset": 10,
            "sort": "desc",
            "apikey": settings.ETHERSCAN_API_KEY
        }
        response = requests.get(settings.ETHERSCAN_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1":
                transactions = data.get("result", [])
                return transactions
            else:
                logger.error(f"Etherscan API error: {data.get('message')}")
                return []
        else:
            logger.error(f"Failed to fetch transactions: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Exception in fetching live transactions: {e}")
        return []


# Process fetched transactions and store new ones into the database with sharding support
def process_transactions(transactions, eth_price, db: Session):
    for txn in transactions:
        txn_hash = txn.get("hash")
        if not txn_hash:
            continue

        # Sharding logic: process transaction only if it belongs to this worker
        try:
            # Remove '0x' prefix if present and convert to integer
            txn_int = int(txn_hash[2:], 16) if txn_hash.startswith("0x") else int(txn_hash, 16)
        except ValueError as e:
            logger.error(f"Invalid transaction hash {txn_hash}: {e}")
            continue

        if txn_int % settings.TOTAL_WORKERS != settings.WORKER_ID:
            # Skip processing if this transaction doesn't belong to this shard
            continue

        # Skip if the transaction already exists in the database
        existing = crud.get_transaction_by_hash(db, txn_hash)
        if existing:
            continue

        try:
            # Calculate fee in ETH: fee = gasUsed * gasPrice / 1e18
            gas_used = int(txn.get("gasUsed", 0))
            gas_price = int(txn.get("gasPrice", 0))
            fee_wei = gas_used * gas_price
            fee_eth = Decimal(fee_wei) / Decimal(10 ** 18)
            fee_usdt = fee_eth * eth_price

            # Convert timestamp string to datetime object
            time_stamp = datetime.fromtimestamp(int(txn.get("timeStamp", 0)))

            transaction_data = schemas.TransactionCreate(
                tx_hash=txn_hash,
                block_number=int(txn.get("blockNumber", 0)),
                time_stamp=time_stamp,
                from_address=txn.get("from"),
                to_address=txn.get("to"),
                gas=int(txn.get("gas", 0)),
                gas_price=gas_price,
                gas_used=gas_used,
                fee_eth=fee_eth,
                fee_usdt=fee_usdt
            )
            crud.create_transaction(db, transaction_data)
            logger.info(f"Stored transaction {txn_hash}")
        except Exception as e:
            logger.error(f"Error processing transaction {txn_hash}: {e}")


# Background thread function for live transaction polling with sharding support
def live_transaction_polling():
    while True:
        db = SessionLocal()
        try:
            eth_price = fetch_eth_price()
            transactions = fetch_live_transactions()
            process_transactions(transactions, eth_price, db)
        except Exception as e:
            logger.error(f"Error in live polling: {e}")
        finally:
            db.close()
        # Wait for the configured polling interval
        time.sleep(settings.POLL_INTERVAL)


# Start the background thread for live polling
def start_background_tasks():
    thread = threading.Thread(target=live_transaction_polling, daemon=True)
    thread.start()
