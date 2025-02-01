import React, { useState } from 'react';

// Component for the transaction query form
function TransactionQueryForm({ onQuery }) {
    const [txHash, setTxHash] = useState('');
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');

    // Handle form submission
    const handleSubmit = (e) => {
        e.preventDefault();
        onQuery({
            tx_hash: txHash,
            start_time: startTime,
            end_time: endTime
        });
    };

    return (
        <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
            <div>
                <label htmlFor="txHash">Transaction Hash:</label>
                <input
                    type="text"
                    id="txHash"
                    value={txHash}
                    onChange={(e) => setTxHash(e.target.value)}
                    placeholder="Enter transaction hash"
                />
            </div>
            <div>
                <label htmlFor="startTime">Start Time:</label>
                <input
                    type="datetime-local"
                    id="startTime"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                />
            </div>
            <div>
                <label htmlFor="endTime">End Time:</label>
                <input
                    type="datetime-local"
                    id="endTime"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                />
            </div>
            <button type="submit">Search</button>
        </form>
    );
}

export default TransactionQueryForm;
