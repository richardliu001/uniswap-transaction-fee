import React, { useState, useEffect } from 'react';
import TransactionQueryForm from './components/TransactionQueryForm';
import TransactionList from './components/TransactionList';
import Summary from './components/Summary';
import { fetchTransactions, fetchSummary } from './services/api';

// Main application component
function App() {
    const [transactions, setTransactions] = useState([]);
    const [summary, setSummary] = useState({ total_fee_eth: 0, total_fee_usdt: 0, current_eth_price: 0 });
    const [queryParams, setQueryParams] = useState({ tx_hash: '', start_time: '', end_time: '', page: 1, page_size: 50 });

    // Load transactions based on query parameters
    const loadTransactions = async (params) => {
        try {
            const data = await fetchTransactions(params);
            setTransactions(data);
        } catch (error) {
            console.error("Error fetching transactions:", error);
        }
    };

    // Load summary information
    const loadSummary = async () => {
        try {
            const data = await fetchSummary();
            setSummary(data);
        } catch (error) {
            console.error("Error fetching summary:", error);
        }
    };

    // Load data when query parameters change
    useEffect(() => {
        loadTransactions(queryParams);
        loadSummary();
    }, [queryParams]);

    // Handle query form submission
    const handleQuery = (params) => {
        setQueryParams({ ...queryParams, ...params, page: 1 });
    };

    // Handle page change
    const handlePageChange = (page) => {
        setQueryParams({ ...queryParams, page });
    };

    // Handle page size change
    const handlePageSizeChange = (page_size) => {
        setQueryParams({ ...queryParams, page_size, page: 1 });
    };

    return (
        <div style={{ padding: '20px' }}>
            <h1>Uniswap Transaction Fee Dashboard</h1>
            <Summary summary={summary} />
            <TransactionQueryForm onQuery={handleQuery} />
            <TransactionList
                transactions={transactions}
                page={queryParams.page}
                pageSize={queryParams.page_size}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
            />
        </div>
    );
}

export default App;
