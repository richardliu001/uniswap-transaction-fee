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
from web3 import Web3

# Configure logger for background tasks
logger = logging.getLogger("background_tasks")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def fetch_eth_price():
    """
    Fetch the current ETH/USDT price from Binance.
    """
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


def fetch_live_transactions():
    """
    Fetch live Uniswap transactions from the Etherscan API.
    """
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


def decode_swap_price(tx_hash: str) -> Decimal:
    """
    Decode the executed swap price for a given transaction hash.
    Connects to an Ethereum node via Infura, fetches the transaction receipt,
    decodes the Uniswap Swap event, and computes the swap price.

    Calculation: swap_price = (sqrtPriceX96 ** 2) / (2 ** 192)
    """
    try:
        # Connect to Ethereum node via Infura using Web3
        w3 = Web3(Web3.HTTPProvider(settings.INFURA_URL))
        if not w3.isConnected():
            logger.error("Web3 is not connected to Infura.")
            return Decimal("0")

        # Get the transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        # Define a simplified Swap event ABI (modify as necessary for your contract)
        swap_event_abi = {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
                {"indexed": False, "internalType": "int256", "name": "amount0", "type": "int256"},
                {"indexed": False, "internalType": "int256", "name": "amount1", "type": "int256"},
                {"indexed": True, "internalType": "address", "name": "recipient", "type": "address"},
                {"indexed": False, "internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
                {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
                {"indexed": False, "internalType": "int24", "name": "tick", "type": "int24"}
            ],
            "name": "Swap",
            "type": "event"
        }

        # Compute the event signature hash
        event_signature_text = "Swap(address,int256,int256,address,uint160,uint128,int24)"
        event_signature_hash = w3.keccak(text=event_signature_text).hex()

        swap_price = Decimal("0")
        # Loop through logs to find the Swap event from the expected contract
        for log in receipt["logs"]:
            if log["address"].lower() == "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640".lower():
                if log["topics"][0].hex() == event_signature_hash:
                    # Create a contract instance with the Swap event ABI
                    contract = w3.eth.contract(
                        address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                        abi=[swap_event_abi]
                    )
                    decoded_event = contract.events.Swap().processLog(log)
                    sqrtPriceX96 = decoded_event["args"]["sqrtPriceX96"]
                    # Compute swap price as (sqrtPriceX96^2) / (2**192)
                    swap_price = Decimal(sqrtPriceX96) ** 2 / Decimal(2 ** 192)
                    break
        return swap_price
    except Exception as e:
        logger.error(f"Error decoding swap price for transaction {tx_hash}: {e}")
        return Decimal("0")


def process_transactions(transactions, eth_price, db: Session):
    """
    Process fetched transactions and store new ones into the database with sharding support.

    Sharding Logic:
    - Convert the transaction hash (a hex string) into an integer.
    - Only process the transaction if (txn_integer % TOTAL_WORKERS) equals WORKER_ID.
    """
    for txn in transactions:
        txn_hash = txn.get("hash")
        if not txn_hash:
            logger.error("Transaction missing hash; skipping.")
            continue

        # Convert the hash from hexadecimal to an integer
        try:
            txn_numeric = int(txn_hash[2:], 16) if txn_hash.startswith("0x") else int(txn_hash, 16)
        except ValueError as e:
            logger.error(f"Invalid transaction hash {txn_hash}: {e}")
            continue

        # Apply sharding: process only if (txn_numeric % TOTAL_WORKERS) == WORKER_ID
        if settings.TOTAL_WORKERS <= 0:
            logger.error("TOTAL_WORKERS must be greater than 0.")
        if txn_numeric % settings.TOTAL_WORKERS != settings.WORKER_ID:
            logger.info(
                f"Skipping transaction {txn_hash} due to sharding: {txn_numeric} % {settings.TOTAL_WORKERS} != {settings.WORKER_ID}.")
            continue

        # Skip if the transaction already exists
        existing = crud.get_transaction_by_hash(db, txn_hash)
        if existing:
            logger.info(f"Transaction {txn_hash} already exists; skipping.")
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
            logger.info(f"Stored transaction {txn_hash} processed by shard {settings.WORKER_ID}.")
        except Exception as e:
            logger.error(f"Error processing transaction {txn_hash}: {e}")


def live_transaction_polling():
    """
    Background thread function for live transaction polling with sharding support.
    It continuously fetches the current ETH price, retrieves live transactions, and processes them.
    """
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
        time.sleep(settings.POLL_INTERVAL)


def start_background_tasks():
    """
    Start the background thread for live transaction polling.
    """
    thread = threading.Thread(target=live_transaction_polling, daemon=True)
    thread.start()
