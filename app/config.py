import os


# Configuration settings for the application
class Settings:
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'mysql')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'uniswap')

    # Etherscan API settings
    ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
    ETHERSCAN_API_URL = "https://api.etherscan.io/api"

    # Binance API URL for fetching ETH/USDT price
    BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"

    # Polling interval in seconds for live transaction fetching
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '60'))

    # Distributed worker configuration for sharded execution
    # WORKER_ID: current instance ID (default 0)
    # TOTAL_WORKERS: total number of deployed instances (default 1)
    WORKER_ID = int(os.getenv('WORKER_ID', '0'))
    TOTAL_WORKERS = int(os.getenv('TOTAL_WORKERS', '1'))


settings = Settings()
