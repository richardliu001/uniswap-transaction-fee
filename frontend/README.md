# Uniswap Transaction Fee Frontend

This is the React-based frontend for querying Uniswap WETH-USDC transaction fees. It provides a query form to search transactions by transaction hash and time range, displays a paginated list of transactions, and shows a summary of total transaction fees (in ETH and USDT) along with the current ETH/USDT price.

## Features

- Query transactions by hash and time range.
- Paginated transaction list.
- Summary display for total transaction fees and current ETH/USDT price.
- Integration with the backend API.
- Dockerized for production deployment.

## Prerequisites

- Node.js and npm (for local development).
- Docker and Docker Compose.

## Setup and Running

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd <repository>/frontend
