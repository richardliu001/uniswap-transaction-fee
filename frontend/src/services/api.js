import axios from 'axios';

// Set the base URL for the backend API; can be overridden by environment variable
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Function to fetch transactions with query parameters
export const fetchTransactions = async (params) => {
    const response = await axios.get(`${API_BASE_URL}/transactions`, { params });
    return response.data;
};

// Function to fetch summary information from the backend
export const fetchSummary = async () => {
    const response = await axios.get(`${API_BASE_URL}/summary`);
    return response.data;
};
