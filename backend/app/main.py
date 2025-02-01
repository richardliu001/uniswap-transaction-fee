from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .routers import transactions
from .database import engine, Base, SessionLocal
from .tasks import start_background_tasks, fetch_eth_price
from . import crud, schemas

# Create all database tables if they do not exist
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Uniswap Transaction Fee API",
    description="API to fetch transaction fees in USDT for Uniswap transactions",
    version="1.0.0"
)

# Include the transactions router
app.include_router(transactions.router)

# Dependency to provide a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint to retrieve summary information
@app.get("/summary", response_model=schemas.Summary)
def get_summary(db: Session = Depends(get_db)):
    total_fee_eth, total_fee_usdt = crud.get_summary(db)
    current_eth_price = fetch_eth_price()
    return schemas.Summary(
        total_fee_eth=total_fee_eth,
        total_fee_usdt=total_fee_usdt,
        current_eth_price=current_eth_price
    )

# Startup event to start background tasks (live polling)
@app.on_event("startup")
def startup_event():
    start_background_tasks()
