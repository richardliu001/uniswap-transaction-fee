import os
import sys
import pytest
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

# Add the project root to sys.path so that the "app" package can be imported.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

###############################################################################
# Override the Database Engine to Use In-Memory SQLite with StaticPool for Testing
###############################################################################

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Create an in-memory SQLite engine that uses a StaticPool.
# This ensures that all connections share the same underlying in-memory database.
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

###############################################################################
# Patch the Database Module to Use the Test Engine and Session
###############################################################################

import app.database as db_mod
db_mod.engine = test_engine
db_mod.SessionLocal = TestingSessionLocal

###############################################################################
# Patch the "created_at" Column Default in the Transaction Model for SQLite
###############################################################################

# Import the Transaction model from app.models
from app.models import Transaction
from sqlalchemy.schema import ColumnDefault

# Remove the server_default (which may return the literal string "CURRENT_TIMESTAMP")
# and set a Python-side default wrapped in a ColumnDefault.
if "created_at" in Transaction.__table__.columns:
    Transaction.__table__.columns["created_at"].server_default = None
    Transaction.__table__.columns["created_at"].default = ColumnDefault(datetime.utcnow)

###############################################################################
# Import Application Modules and Create the Test Client
###############################################################################

from app.main import app
from app.database import Base
from app import crud, schemas
from fastapi.testclient import TestClient

# Create a TestClient instance for the FastAPI application.
client = TestClient(app)

###############################################################################
# Fixtures
###############################################################################

@pytest.fixture(scope="module")
def test_db():
    """
    Fixture: Set up and tear down the test database.
    Uses an in-memory SQLite database (with StaticPool) so that all sessions share the same data.
    Creates all tables before tests and drops them after tests.
    """
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(autouse=True)
def clear_db(test_db):
    """
    Fixture: Clear the database between tests.
    This fixture drops and re-creates all tables after each test to ensure test isolation.
    """
    yield
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

###############################################################################
# Helper Function for Decimal Rounding
###############################################################################

def quantize_decimal(value, exp="0.00001"):
    """
    Helper function to quantize a Decimal value to a fixed exponent.
    """
    return Decimal(value).quantize(Decimal(exp), rounding=ROUND_HALF_UP)

###############################################################################
# Test Cases
###############################################################################

def test_get_transactions(test_db):
    """
    Test the GET /transactions endpoint:
    Verify that an inserted test transaction is returned correctly.
    """
    # Insert a test transaction.
    test_tx = schemas.TransactionCreate(
        tx_hash="0xtesthash",
        block_number=123456,
        time_stamp=datetime.utcnow(),
        from_address="0xfrom",
        to_address="0xto",
        gas=21000,
        gas_price=1000000000,
        gas_used=21000,
        fee_eth=Decimal("0.00021"),
        fee_usdt=Decimal("0.63")
    )
    crud.create_transaction(test_db, test_tx)

    # Call the GET /transactions endpoint with tx_hash as a query parameter.
    response = client.get("/transactions", params={"tx_hash": "0xtesthash"})
    assert response.status_code == 200, f"Response status code: {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    assert len(data) >= 1, "The returned list should have at least one item"
    assert data[0]["tx_hash"] == "0xtesthash", "Returned transaction hash does not match"

def test_get_transaction_by_hash(test_db):
    """
    Test the GET /transactions/{tx_hash} endpoint:
    Verify that a transaction can be retrieved correctly by its hash.
    """
    # Insert a test transaction.
    test_tx = schemas.TransactionCreate(
        tx_hash="0xuniquehash",
        block_number=654321,
        time_stamp=datetime.utcnow(),
        from_address="0xabc",
        to_address="0xdef",
        gas=21000,
        gas_price=2000000000,
        gas_used=21000,
        fee_eth=Decimal("0.00042"),
        fee_usdt=Decimal("1.26")
    )
    crud.create_transaction(test_db, test_tx)

    # Call the GET /transactions/{tx_hash} endpoint.
    response = client.get("/transactions/0xuniquehash")
    assert response.status_code == 200, f"Response status code: {response.status_code}"
    data = response.json()
    assert data["tx_hash"] == "0xuniquehash", "Returned transaction hash does not match"
    assert data["block_number"] == 654321, "Returned block_number does not match"

def test_get_summary(test_db):
    """
    Test the GET /summary endpoint:
    Verify that the summary information (total fees and current ETH price) is computed correctly.
    """
    # Insert two test transactions.
    tx1 = schemas.TransactionCreate(
        tx_hash="0xtx1",
        block_number=111111,
        time_stamp=datetime.utcnow(),
        from_address="0x1",
        to_address="0x2",
        gas=21000,
        gas_price=1000000000,
        gas_used=21000,
        fee_eth=Decimal("0.00021"),
        fee_usdt=Decimal("0.63")
    )
    tx2 = schemas.TransactionCreate(
        tx_hash="0xtx2",
        block_number=222222,
        time_stamp=datetime.utcnow(),
        from_address="0x3",
        to_address="0x4",
        gas=21000,
        gas_price=1000000000,
        gas_used=21000,
        fee_eth=Decimal("0.00021"),
        fee_usdt=Decimal("0.63")
    )
    crud.create_transaction(test_db, tx1)
    crud.create_transaction(test_db, tx2)

    # Call the GET /summary endpoint.
    response = client.get("/summary")
    assert response.status_code == 200, f"Response status code: {response.status_code}"
    data = response.json()
    # Expected values
    expected_fee_eth = Decimal("0.00042")
    expected_fee_usdt = Decimal("1.26")
    # Compare rounded (quantized) decimals to avoid precision issues.
    actual_fee_eth = quantize_decimal(data["total_fee_eth"])
    actual_fee_usdt = quantize_decimal(data["total_fee_usdt"])
    assert actual_fee_eth == quantize_decimal(expected_fee_eth), "Total fee (ETH) does not match"
    assert actual_fee_usdt == quantize_decimal(expected_fee_usdt), "Total fee (USDT) does not match"
    # Ensure the current ETH price is a positive value.
    assert Decimal(data["current_eth_price"]) > Decimal("0"), "Current ETH price should be greater than 0"

def test_historical_endpoint(test_db):
    """
    Test the POST /transactions/historical endpoint:
    Verify that the historical processing endpoint returns the expected message.
    """
    # Set start_time and end_time in ISO format.
    start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end_time = datetime.utcnow().isoformat()

    # Call the POST /transactions/historical endpoint.
    response = client.post("/transactions/historical", params={"start_time": start_time, "end_time": end_time})
    assert response.status_code == 200, f"Response status code: {response.status_code}"
    data = response.json()
    assert "message" in data, "Response should contain a 'message' field"
    assert data["message"].startswith("Historical processing initiated"), "Returned message does not match expected text"
