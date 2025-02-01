from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .routers import transactions
from .database import engine, Base, SessionLocal
from .tasks import start_background_tasks, fetch_eth_price  # and start_background_tasks covers polling
from . import crud, schemas

# Create all database tables if they do not exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Uniswap Transaction Fee API",
    description="API to fetch transaction fees in USDT for Uniswap transactions and decode swap prices.",
    version="1.0.0"
)

app.include_router(transactions.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/summary", response_model=schemas.Summary)
def get_summary(db: Session = Depends(get_db)):
    total_fee_eth, total_fee_usdt = crud.get_summary(db)
    current_eth_price = fetch_eth_price()
    return schemas.Summary(
        total_fee_eth=total_fee_eth,
        total_fee_usdt=total_fee_usdt,
        current_eth_price=current_eth_price
    )

@app.on_event("startup")
def startup_event():
    # Start background tasks for live polling.
    start_background_tasks()
