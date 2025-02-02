import time
import threading
import requests
from datetime import datetime, timedelta
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
    Fetch live Uniswap transactions from the Etherscan API using pagination.

    This function loops through pages until no more transactions are returned.
    Returns:
        A list of transaction dictionaries.
    """
    all_transactions = []
    page = 1
    offset = 100  # Retrieve more transactions per page for live data
    while True:
        try:
            params = {
                "module": "account",
                "action": "tokentx",
                "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                "page": page,
                "offset": offset,
                "sort": "desc",  # Most recent transactions first
                "apikey": settings.ETHERSCAN_API_KEY
            }
            response = requests.get(settings.ETHERSCAN_API_URL, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch transactions on page {page}: {response.status_code}")
                break
            data = response.json()
            if data.get("status") != "1":
                logger.error(f"Etherscan API error on page {page}: {data.get('message')}")
                break
            transactions = data.get("result", [])
            if not transactions:
                logger.info("No more live transactions found.")
                break
            all_transactions.extend(transactions)
            # If fewer transactions than requested are returned, no more pages are available.
            if len(transactions) < offset:
                break
            page += 1
        except Exception as e:
            logger.error(f"Exception while paginating transactions on page {page}: {e}")
            break
    return all_transactions


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
    Additionally, after storing the transaction, decode and update the swap price.
    """
    for txn in transactions:
        txn_hash = txn.get("hash")
        if not txn_hash:
            logger.error("Transaction missing hash; skipping.")
            continue

        # Convert the hash from hexadecimal to an integer.
        try:
            txn_numeric = int(txn_hash[2:], 16) if txn_hash.startswith("0x") else int(txn_hash, 16)
        except ValueError as e:
            logger.error(f"Invalid transaction hash {txn_hash}: {e}")
            continue

        # Apply sharding: process only if (txn_numeric % TOTAL_WORKERS) == WORKER_ID.
        if settings.TOTAL_WORKERS <= 0:
            logger.error("TOTAL_WORKERS must be greater than 0.")
        if txn_numeric % settings.TOTAL_WORKERS != settings.WORKER_ID:
            logger.info(
                f"Skipping transaction {txn_hash} due to sharding: {txn_numeric} % {settings.TOTAL_WORKERS} != {settings.WORKER_ID}.")
            continue

        # Skip if the transaction already exists.
        existing = crud.get_transaction_by_hash(db, txn_hash)
        if existing:
            logger.info(f"Transaction {txn_hash} already exists; skipping.")
            continue

        try:
            # Calculate fee in ETH: fee = gasUsed * gasPrice / 1e18.
            gas_used = int(txn.get("gasUsed", 0))
            gas_price = int(txn.get("gasPrice", 0))
            fee_wei = gas_used * gas_price
            fee_eth = Decimal(fee_wei) / Decimal(10 ** 18)
            fee_usdt = fee_eth * eth_price

            # Convert timestamp string to a datetime object.
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
            # Create transaction record in the database.
            crud.create_transaction(db, transaction_data)
            logger.info(f"Stored transaction {txn_hash} processed by shard {settings.WORKER_ID}.")

            # Decode the swap price for this transaction and update the record.
            swap_price = decode_swap_price(txn_hash)
            if swap_price > Decimal("0"):
                crud.update_swap_price(db, txn_hash, swap_price)
                logger.info(f"Updated transaction {txn_hash} with swap price {swap_price}.")
            else:
                logger.info(f"Swap price for transaction {txn_hash} is 0; not updated.")
        except Exception as e:
            logger.error(f"Error processing transaction {txn_hash}: {e}")


def live_transaction_polling():
    """
    Background thread function for live transaction polling with sharding support.
    It continuously fetches the current ETH price, retrieves live transactions (using pagination),
    compares with the latest processed timestamp from the database to avoid duplicates,
    and processes new transactions.
    """
    from sqlalchemy import func
    from app.models import Transaction

    while True:
        db = SessionLocal()
        try:
            eth_price = fetch_eth_price()
            # Use pagination to fetch all available transactions.
            all_transactions = []
            page = 1
            offset = 100  # Retrieve more transactions per page for live data.
            while True:
                try:
                    params = {
                        "module": "account",
                        "action": "tokentx",
                        "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                        "page": page,
                        "offset": offset,
                        "sort": "desc",  # Most recent transactions first.
                        "apikey": settings.ETHERSCAN_API_KEY
                    }
                    response = requests.get(settings.ETHERSCAN_API_URL, params=params, timeout=10)
                    if response.status_code != 200:
                        logger.error(f"Failed to fetch transactions on page {page}: {response.status_code}")
                        break
                    data = response.json()
                    if data.get("status") != "1":
                        logger.error(f"Etherscan API error on page {page}: {data.get('message')}")
                        break
                    transactions = data.get("result", [])
                    if not transactions:
                        logger.info("No more live transactions found.")
                        break
                    all_transactions.extend(transactions)
                    # If fewer transactions than requested are returned, no more pages available.
                    if len(transactions) < offset:
                        break
                    page += 1
                except Exception as e:
                    logger.error(f"Exception while paginating transactions on page {page}: {e}")
                    break

            # Query the latest processed transaction timestamp from the database.
            latest_tx = db.query(func.max(Transaction.time_stamp)).scalar()
            ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
            if latest_tx is not None:
                # Use the later of the latest transaction timestamp or 10 minutes ago.
                if latest_tx < ten_minutes_ago:
                    latest_ts = int(ten_minutes_ago.timestamp())
                else:
                    latest_ts = int(latest_tx.timestamp())
            else:
                latest_ts = 0

            # Filter transactions: only process those with timeStamp > latest_ts.
            filtered_transactions = []
            for txn in all_transactions:
                txn_ts = int(txn.get("timeStamp", 0))
                if txn_ts > latest_ts:
                    filtered_transactions.append(txn)
                else:
                    logger.info(
                        f"Skipping transaction {txn.get('hash')} because timestamp {txn_ts} <= latest processed {latest_ts}.")

            process_transactions(filtered_transactions, eth_price, db)
        except Exception as e:
            logger.error(f"Error in live polling: {e}")
        finally:
            db.close()
        time.sleep(settings.POLL_INTERVAL)


def process_historical_transactions(start_time: datetime, end_time: datetime, db: Session):
    """
    Process historical transactions between start_time and end_time.
    This function fetches transactions in batch pages using the Etherscan API.

    It repeatedly requests pages until:
      - No transactions are returned, or
      - The oldest transaction in a page is older than start_time.

    For each transaction in the returned page, if its timestamp is between start_time and end_time
    and not already in the database, the transaction is processed and stored.

    Returns the total number of processed transactions.
    """
    processed_count = 0
    page = 1
    offset = 100  # Retrieve more transactions per page for historical data.
    while True:
        try:
            params = {
                "module": "account",
                "action": "tokentx",
                "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                "page": page,
                "offset": offset,
                "sort": "asc",  # Ascending order: older transactions first.
                "apikey": settings.ETHERSCAN_API_KEY
            }
            response = requests.get(settings.ETHERSCAN_API_URL, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch historical transactions on page {page}: {response.status_code}")
                break
            data = response.json()
            if data.get("status") != "1":
                logger.error(f"Etherscan API error (historical) on page {page}: {data.get('message')}")
                break
            transactions = data.get("result", [])
            if not transactions:
                logger.info("No more historical transactions found.")
                break

            # Convert start_time and end_time to UNIX timestamps.
            start_ts = int(start_time.timestamp())
            end_ts = int(end_time.timestamp())

            transactions_in_range = []
            for txn in transactions:
                txn_ts = int(txn.get("timeStamp", 0))
                # Process transaction only if it falls within the specified time range.
                if start_ts <= txn_ts <= end_ts:
                    # Check database for duplicates.
                    if crud.get_transaction_by_hash(db, txn.get("hash")) is None:
                        transactions_in_range.append(txn)
            if not transactions_in_range:
                # If the oldest transaction in this page is older than start_time, exit loop.
                oldest_txn_ts = int(transactions[0].get("timeStamp", 0))
                if oldest_txn_ts < start_ts:
                    break

            eth_price_current = fetch_eth_price()
            process_transactions(transactions_in_range, eth_price_current, db)
            processed_count += len(transactions_in_range)
            logger.info(f"Processed {len(transactions_in_range)} historical transactions from page {page}.")
            # If fewer transactions than requested are returned, no more pages available.
            if len(transactions) < offset:
                break
            page += 1
        except Exception as e:
            logger.error(f"Error processing historical transactions on page {page}: {e}")
            break
    return processed_count


def start_historical_processing(start_time: datetime, end_time: datetime):
    """
    Start a batch job to process historical transactions within a given time range.
    This function runs in a separate thread.
    """

    def run():
        db = SessionLocal()
        try:
            count = process_historical_transactions(start_time, end_time, db)
            logger.info(f"Historical processing completed. Total processed transactions: {count}")
        except Exception as e:
            logger.error(f"Error in historical processing: {e}")
        finally:
            db.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def start_background_tasks():
    """
    Start the background thread for live transaction polling.
    """
    thread = threading.Thread(target=live_transaction_polling, daemon=True)
    thread.start()
