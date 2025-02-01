-- SQL script to create the 'transactions' table in MySQL

CREATE TABLE `transactions` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `tx_hash` VARCHAR(255) NOT NULL,
    `block_number` VARCHAR(50) DEFAULT NULL,
    `time_stamp` DATETIME NOT NULL,
    `from_address` VARCHAR(255) DEFAULT NULL,
    `to_address` VARCHAR(255) DEFAULT NULL,
    `gas_used` INT NOT NULL,
    `gas_price` INT NOT NULL,
    `fee_eth` DECIMAL(20,10) NOT NULL,
    `fee_usdt` DECIMAL(20,10) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_tx_hash` (`tx_hash`),
    KEY `idx_time_stamp` (`time_stamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
