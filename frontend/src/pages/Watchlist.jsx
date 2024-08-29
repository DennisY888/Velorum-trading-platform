import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';
import "../styles/Watchlist.css";
import { useNavigate } from 'react-router-dom';

const Watchlist = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 6;
  const navigate = useNavigate();

  const fetchWatchlist = useCallback(async () => {
    console.log('Fetching watchlist with offset:', offset);
    setLoading(true);
    try {
      const response = await api.get('/api/watchlist/my_watchlist/', {
        params: { limit, offset }
      });

      setWatchlist(prev => offset === 0 ? response.data.results : [...prev, ...response.data.results]);
      setHasMore(response.data.next !== null);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    } finally {
      setLoading(false);
    }
  }, [offset]);

  const fetchUpdatedStockData = useCallback(async () => {
    try {
      const updatedWatchlist = await Promise.all(
        watchlist.map(async (stock) => {
          const response = await api.get(`/api/quote/${stock.symbol}/`);
          return {
            ...stock,
            current_price: response.data.current_price,
            daily_change: response.data.daily_change
          };
        })
      );
      setWatchlist(updatedWatchlist);
    } catch (error) {
      console.error('Error fetching updated stock data:', error);
    }
  }, [watchlist]);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  useEffect(() => {
    const intervalId = setInterval(fetchUpdatedStockData, 60000); // Fetch updates every minute

    return () => clearInterval(intervalId); // Cleanup interval on component unmount
  }, [fetchUpdatedStockData]);

  const handleScroll = useCallback(() => {
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight) {
      if (hasMore && !loading) {
        setOffset(prev => prev + limit);
      }
    }
  }, [hasMore, loading, limit]);

  useEffect(() => {
    const debouncedHandleScroll = debounce(handleScroll, 200);
    window.addEventListener('scroll', debouncedHandleScroll);

    return () => window.removeEventListener('scroll', debouncedHandleScroll);
  }, [handleScroll]);

  const handleClick = useCallback((symbol) => {
    navigate(`/quote?symbol=${symbol}&action=watch`);
  }, [navigate]);

  return (
    <div className="watchlist-container">
      <h1>My Watchlist</h1>
      <div className="watchlist-grid">
        {watchlist.map(stock => (
          <StockCard key={stock.symbol} stock={stock} onClick={handleClick} />
        ))}
      </div>
      {loading && <div className="loading-spinner"></div>}
      {!hasMore && <p>No more stocks to load</p>}
    </div>
  );
};

const StockCard = React.memo(({ stock, onClick }) => (
  <div className="stock-card" onClick={() => onClick(stock.symbol)}>
    <h2>{stock.symbol}</h2>
    <p>{stock.name}</p>
    <p>Current Price: ${stock.current_price}</p>
    <p>Daily Change: {stock.daily_change.toFixed(2)}%</p>
  </div>
));

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

export default Watchlist;
