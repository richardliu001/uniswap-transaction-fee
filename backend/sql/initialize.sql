CREATE DATABASE IF NOT EXISTS uniswap;
USE uniswap;

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tx_hash VARCHAR(66) NOT NULL UNIQUE,
    block_number BIGINT NOT NULL,
    time_stamp DATETIME NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    gas BIGINT NOT NULL,
    gas_price BIGINT NOT NULL,
    gas_used BIGINT NOT NULL,
    fee_eth DECIMAL(30, 18) NOT NULL,
    fee_usdt DECIMAL(30, 18) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    swap_price DECIMAL(30, 18) NULL
);