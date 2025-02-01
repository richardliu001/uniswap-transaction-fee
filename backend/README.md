# Uniswap Transaction Fee Dashboard

This project is a full-stack application that tracks and displays transaction fees in USDT for all Uniswap WETH-USDC transactions. The backend is built with Python (FastAPI) and the frontend with React.

## Architecture Overview

- **Backend (Python / FastAPI)**
  - Provides RESTful API endpoints to fetch transaction data.
  - Continuously fetches live transaction data from the Etherscan API in a background task.
  - Calculates transaction fee in ETH and converts it to USDT using the current ETH/USDT price from the Binance API.
  - Uses SQLite as the database (via SQLAlchemy ORM) to store transaction records.
  - Endpoints:
    - `GET /transaction/{tx_hash}`: Fetch a transaction by its hash.
    - `GET /transactions`: Fetch transactions with optional time filters and pagination.
    - `GET /summary`: Fetch summary data including total fees and current ETH/USDT price.
  - Automatic API documentation is available at `/docs`.

- **Frontend (React)**
  - A single page application that allows users to search for transactions by hash or time range.
  - Displays a paginated list of transactions.
  - Shows a summary including total transaction fees (in USDT and ETH) and the current ETH/USDT price.

- **Dockerization**
  - The application is containerized using Docker and managed with `docker-compose`.
  - The backend and frontend run in separate containers.

## Prerequisites

- Docker and Docker Compose installed on your machine.
- An Etherscan API key. (Set this in the `docker-compose.yml` or via environment variables.)

## Getting Started

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd <repository_directory>
