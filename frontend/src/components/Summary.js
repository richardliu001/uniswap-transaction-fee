import React from 'react';

// Component to display summary information
function Summary({ summary }) {
    return (
        <div style={{ marginBottom: '20px' }}>
            <h2>Summary</h2>
            <p>Total Transaction Fee (ETH): {summary.total_fee_eth}</p>
            <p>Total Transaction Fee (USDT): {summary.total_fee_usdt}</p>
            <p>Current ETH/USDT Price: {summary.current_eth_price}</p>
        </div>
    );
}

export default Summary;
