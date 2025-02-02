# Uniswap Transaction Fee and Swap Price API

This full-stack system is designed to track Uniswap transactions and extract important financial data. It calculates transaction fees in ETH and USDT and decodes the actual executed swap price from Uniswap Swap events. The system supports:

- **Real‑Time Data Ingestion:** Continuously records live transactions using the Etherscan API with sharding support to avoid duplicate processing in distributed deployments.
- **Historical Batch Processing:** Processes historical transaction data within a specified time range via a dedicated RESTful API endpoint.
- **Swap Price Decoding:** Uses Infura and web3.py to connect to an Ethereum node and decode the Swap event to calculate the swap price with the formula:  
  \[
  \text{swap\_price} = \frac{(\text{sqrtPriceX96})^2}{2^{192}}
  \]
- **RESTful API Endpoints:** Exposes endpoints to query transactions, summary data, and the decoded swap price for a given transaction hash.
- **Containerized Deployment:** Docker Compose orchestrates all components (MySQL, multiple backend instances, Nginx as reverse proxy, and frontend).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Installation and Running Locally](#installation-and-running-locally)
- [Docker Compose Deployment](#docker-compose-deployment)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Additional Notes](#additional-notes)
- [License](#license)

---

## Overview

This project provides a production‑ready backend built with FastAPI and SQLAlchemy, along with a React frontend (not detailed here) that together enable:
- Recording live Uniswap transactions and calculating fees.
- Decoding the executed swap price from transaction logs.
- Processing historical transaction data on demand.
- Distributing processing across multiple backend instances using sharding logic.

---

## Architecture

- **Backend:**  
  - **FastAPI:** Provides RESTful API endpoints and background tasks.
  - **SQLAlchemy:** Handles ORM interactions with MySQL.
  - **Background Tasks:** Polls live transaction data and processes historical data.
  - **Infura & web3.py:** Used for connecting to Ethereum nodes and decoding Uniswap Swap events.
  
- **Frontend:**  
  - **React:** A one-page application that queries the backend API to display transactions, summaries, and swap prices.
  
- **Containerization:**  
  - **Docker Compose:** Orchestrates MySQL, multiple backend containers (each with sharding configured), an Nginx reverse proxy for load balancing, and the frontend.

---

## Directory Structure

```
assignment/                # Project root
├── docker-compose.yml     # Docker Compose configuration
├── README.md              # This file
├── requirements.txt       # Production dependencies (includes web3, FastAPI, etc.)
├── sql/
│   └── initialize.sql     # Database initialization scripts for MySQL
└── backend/
    ├── __init__.py        # (empty)
    ├── config.py          # Configuration (includes INFURA_URL, API keys, etc.)
    ├── database.py        # SQLAlchemy setup (Base, engine, SessionLocal)
    ├── models.py          # Database models (Transaction with swap_price field)
    ├── schemas.py         # Pydantic models (including SwapPriceResponse)
    ├── crud.py            # CRUD operations (including update_swap_price)
    ├── tasks.py           # Background tasks for live and historical processing, decoding swap price
    ├── main.py            # FastAPI application entry point (includes startup event)
    └── routers/
        ├── __init__.py    # (empty)
        └── transactions.py  # API routes for transactions
```

---

## Prerequisites

- **Docker & Docker Compose:** Version 20.x or later.
- **Python:** Version 3.9 or higher.
- **Node.js & npm:** For building and running the frontend.
- **Infura Account:** You must have an Infura project ID to connect to Ethereum nodes.
- **Etherscan & Binance API Keys:** Required to fetch transaction and price data.

---

## Configuration

### Environment Variables

The configuration is mainly handled in `backend/app/config.py`. Key settings include:

- **Database Settings:**
  - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  
- **API Keys:**
  - `ETHERSCAN_API_KEY`: Your Etherscan API key.
  - `BINANCE_API_URL`: Predefined Binance URL for ETH/USDT price.
  
- **Polling and Sharding:**
  - `POLL_INTERVAL`: Interval (in seconds) for live polling.
  - `WORKER_ID` and `TOTAL_WORKERS`: For sharding support in multi‑instance deployments.
  
- **Infura URL:**
  - `INFURA_URL`: Must be set to  
    ```
    https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
    ```
    Replace `YOUR_INFURA_PROJECT_ID` with your actual Infura project ID.

### Docker Compose Environment

In the Docker Compose file, each backend container should have the environment variable `INFURA_URL` properly set. See the updated Docker Compose section below.

---

## Installation and Running Locally

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd assignment
   ```

2. **Backend Setup:**

   - Create and activate a Python virtual environment:
     ```bash
     python -m venv .venv
     source .venv/bin/activate   # On Windows: .venv\Scripts\activate
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - (Optional) Run the backend locally:
     ```bash
     uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
     ```

3. **Frontend Setup:**

   - Navigate to the frontend directory:
     ```bash
     cd frontend
     ```
   - Install dependencies:
     ```bash
     npm install
     ```
   - Run the frontend locally:
     ```bash
     npm start
     ```
   - The frontend will be available at [http://localhost:3000](http://localhost:3000).

---

## Docker Compose Deployment

The provided `docker-compose.yml` orchestrates the entire stack. An updated example is shown below:

```yaml
version: "3.8"

services:
  mysql:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: uniswap
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/sql:/docker-entrypoint-initdb.d
    networks:
      - backend_net

  backend1:
    build: ./backend
    depends_on:
      - mysql
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: root
      DB_PASSWORD: password
      DB_NAME: uniswap
      ETHERSCAN_API_KEY: your_etherscan_api_key
      POLL_INTERVAL: 60
      WORKER_ID: 0
      TOTAL_WORKERS: 3
      INFURA_URL: "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    networks:
      - backend_net
    restart: always

  backend2:
    build: ./backend
    depends_on:
      - mysql
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: root
      DB_PASSWORD: password
      DB_NAME: uniswap
      ETHERSCAN_API_KEY: your_etherscan_api_key
      POLL_INTERVAL: 60
      WORKER_ID: 1
      TOTAL_WORKERS: 3
      INFURA_URL: "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    networks:
      - backend_net
    restart: always

  backend3:
    build: ./backend
    depends_on:
      - mysql
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: root
      DB_PASSWORD: password
      DB_NAME: uniswap
      ETHERSCAN_API_KEY: your_etherscan_api_key
      POLL_INTERVAL: 60
      WORKER_ID: 2
      TOTAL_WORKERS: 3
      INFURA_URL: "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    networks:
      - backend_net
    restart: always

  nginx:
    image: nginx:alpine
    depends_on:
      - backend1
      - backend2
      - backend3
    ports:
      - "8000:8000"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - backend_net
    restart: always

  frontend:
    build: ./frontend
    depends_on:
      - nginx
    environment:
      REACT_APP_API_BASE_URL: http://nginx:8000
    ports:
      - "3000:3000"
    networks:
      - backend_net
    restart: always

volumes:
  mysql_data:

networks:
  backend_net:
```

### To Build and Run All Services:

```bash
docker-compose up --build
```

- **MySQL** is available on port 3306.
- **Backend API** is exposed via Nginx on port 8000.
- **Frontend** is available on port 3000.

---

## API Endpoints

### Base URL

- When running via Docker Compose, the backend API is accessible at [http://localhost:8000](http://localhost:8000).

### Main Endpoints

- **GET `/transactions`**  
  Retrieve a paginated list of transactions.  
  Query parameters include:
  - `tx_hash`: Filter by transaction hash.
  - `start_time`: Filter by starting time (ISO format).
  - `end_time`: Filter by ending time (ISO format).
  - `page` and `page_size`: For pagination.

- **GET `/transactions/{tx_hash}`**  
  Retrieve a specific transaction by its hash.

- **GET `/transactions/swapprice/{tx_hash}`**  
  Retrieve the decoded swap price for the specified transaction.  
  If the swap price is not already stored, it will be decoded on the fly via Infura and updated in the database.

- **GET `/summary`**  
  Retrieve a summary including total fees (ETH and USDT) and the current ETH/USDT price.

- **POST `/historical`**  
  Trigger historical batch processing for transactions within a specified time range.  
  **Request Parameters:**  
  - `start_time` (datetime in ISO format)
  - `end_time` (datetime in ISO format)  
  **Response:** A JSON message indicating that historical processing has been initiated.

### Swagger Documentation

- You can view the automatically generated API documentation via Swagger UI at:  
  [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Usage Examples

### Real‑Time Data Ingestion

When the backend service starts, it automatically launches a background thread via `start_background_tasks()` that continuously polls the Etherscan API for live transactions. It uses pagination to retrieve as many recent transactions as possible and applies sharding logic to avoid duplicate processing in a distributed deployment. New transactions are stored in the database, and if possible, the swap price is decoded and saved.

### Historical Batch Processing

You can trigger historical data processing by sending a POST request to `/historical` with the desired time range. For example, using Swagger UI or curl:

```bash
curl -X POST "http://localhost:8000/historical?start_time=2023-01-01T00:00:00&end_time=2023-01-07T23:59:59"
```

This will start a background thread that retrieves historical transactions (using pagination and filtering based on timestamps), processes them (avoiding duplicates by checking against existing database records), and logs the number of processed transactions.

### Retrieving Swap Price

To get the decoded swap price for a particular transaction, use the GET endpoint:

```bash
curl "http://localhost:8000/transactions/swapprice/0xTRANSACTION_HASH"
```

If the swap price is not already stored, the system will decode it (via Infura) and update the record before returning the result.

---

## Testing

You can run tests using pytest. Make sure your virtual environment is activated and run:

```bash
pytest backend/tests/test_transactions.py
```

This test suite includes tests for:
- Retrieving transactions
- Retrieving a transaction by hash
- Checking summary data
- Triggering historical processing (stub)
- Testing the swap price decoding endpoint (with monkeypatch to simulate decoding)

---

## Additional Notes

- **Infura Configuration:**  
  Ensure that the `INFURA_URL` environment variable is set correctly in your configuration and Docker Compose file. It should be in the format:  
  `https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID`

- **API Keys:**  
  Set your `ETHERSCAN_API_KEY` and other sensitive values in the environment or Docker Compose configuration.

- **Sharding Logic:**  
  The system uses the remainder of the transaction hash (converted to an integer) modulo `TOTAL_WORKERS` compared with `WORKER_ID` to ensure that in a distributed environment only a subset of transactions are processed by each backend instance.

- **Data Duplication:**  
  Both live and historical processing functions check the database for existing transactions (by hash and by latest processed timestamp) to avoid inserting duplicate data.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
