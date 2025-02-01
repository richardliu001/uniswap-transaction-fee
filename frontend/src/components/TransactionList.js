import React from 'react';

// Component for displaying a paginated list of transactions
function TransactionList({ transactions, page, pageSize, onPageChange, onPageSizeChange }) {
    // Handle page navigation
    const handlePageChange = (newPage) => {
        onPageChange(newPage);
    };

    // Handle page size selection
    const handlePageSizeChange = (e) => {
        onPageSizeChange(parseInt(e.target.value, 10));
    };

    return (
        <div>
            <h2>Transactions</h2>
            <table border="1" cellPadding="5" cellSpacing="0">
                <thead>
                    <tr>
                        <th>Transaction Hash</th>
                        <th>Block Number</th>
                        <th>Timestamp</th>
                        <th>Fee (ETH)</th>
                        <th>Fee (USDT)</th>
                    </tr>
                </thead>
                <tbody>
                    {transactions.length > 0 ? (
                        transactions.map((txn) => (
                            <tr key={txn.tx_hash}>
                                <td>{txn.tx_hash}</td>
                                <td>{txn.block_number}</td>
                                <td>{new Date(txn.time_stamp).toLocaleString()}</td>
                                <td>{txn.fee_eth}</td>
                                <td>{txn.fee_usdt}</td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="5">No transactions found.</td>
                        </tr>
                    )}
                </tbody>
            </table>
            <div style={{ marginTop: '10px' }}>
                <label htmlFor="pageSize">Page Size: </label>
                <select id="pageSize" value={pageSize} onChange={handlePageSizeChange}>
                    <option value="10">10</option>
                    <option value="25">25</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                </select>
            </div>
            <div style={{ marginTop: '10px' }}>
                <button onClick={() => handlePageChange(page > 1 ? page - 1 : 1)}>Previous</button>
                <span style={{ margin: '0 10px' }}>Page {page}</span>
                <button onClick={() => handlePageChange(page + 1)}>Next</button>
            </div>
        </div>
    );
}

export default TransactionList;
