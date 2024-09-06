import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';
import "../styles/History.css";

const History = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const limit = 10;



  const fetchTransactions = useCallback(async () => {
    console.log('Fetching transactions with offset:', offset);
    setLoading(true);
    try {
      const response = await api.get('/api/history/my_history/', {
        params: { limit, offset }
      });

      setTransactions(prev => offset === 0 ? response.data.results : [...prev, ...response.data.results]);
      setHasMore(response.data.next !== null);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  }, [offset]);



  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);



  const handleScroll = useCallback(() => {
    const tableContainer = document.querySelector('.table-container');
    if (tableContainer.scrollHeight - tableContainer.scrollTop === tableContainer.clientHeight) {
      if (hasMore && !loading) {
        setOffset(prev => prev + limit);
      }
    }
  }, [hasMore, loading, limit]);



  useEffect(() => {
    const tableContainer = document.querySelector('.table-container');
    const debouncedHandleScroll = debounce(handleScroll, 200);
    tableContainer.addEventListener('scroll', debouncedHandleScroll);

    return () => tableContainer.removeEventListener('scroll', debouncedHandleScroll);
  }, [handleScroll]);



  return (
    <div className="transaction-history-container">
      <h1 className='font-bold text-white text-2xl mb-3 mt-6'>Transaction History</h1>
      <div className="table-container">
        <table className="transaction-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Company Name</th>
              <th>Method</th>
              <th>Shares</th>
              <th>Price per Share</th>
              <th>Total Value</th>
              <th>Date/Time</th>
              <th>Remaining Cash</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map(transaction => (
              <TransactionRow key={transaction.id} transaction={transaction} />
            ))}
          </tbody>
        </table>
      </div>
      {loading && <div className='loading-spinner'></div>}
      {!hasMore && <p className="text-gray-400 mt-6">No more transactions to load</p>}
      {hasMore && <p className="text-gray-400 mt-6">Scroll down for more</p>}
    </div>
  );
};



const TransactionRow = React.memo(({ transaction }) => {
  // Determine the row class based on the transaction method
  const rowClass = transaction.method.toLowerCase() === "buy" ? "row-buy" : "row-sell";

  return (
    <tr className={rowClass}>
      <td>{transaction.symbol}</td>
      <td>{transaction.name}</td>
      <td>{transaction.method.toUpperCase()}</td>
      <td>{transaction.shares}</td>
      <td>{transaction.price}</td>
      <td>{transaction.total_value}</td>
      <td>{new Date(transaction.transacted).toLocaleString()}</td>
      <td>{transaction.new_cash}</td>
    </tr>
  );
});





const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export default History;
