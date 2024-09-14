import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import debounce from 'lodash.debounce';
import "../styles/Watchlist.css";



const Watchlist = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(false); // For initial loading
  const [scrollLoading, setScrollLoading] = useState(false); // New state for scroll loading
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 9;
  const navigate = useNavigate();



  const fetchWatchlist = useCallback(async () => {
    if (offset === 0) {
      setLoading(true); // Set loading only for initial load
    } else {
      setScrollLoading(true); // Set scroll loading spinner only for additional data
    }

    try {
      const response = await api.get('/api/watchlist/my_watchlist/', {
        params: { limit, offset }
      });

      setWatchlist(prev => offset === 0 ? response.data.results : [...prev, ...response.data.results]);
      setHasMore(response.data.next !== null);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    } finally {
      setLoading(false); // Stop loading for initial load
      setScrollLoading(false); // Stop loading for scroll fetch
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
    const intervalId = setInterval(fetchUpdatedStockData, 40000); // Fetch updates every minute
    return () => clearInterval(intervalId); // Cleanup interval on component unmount
  }, [fetchUpdatedStockData]);



  const handleScroll = useCallback(() => {
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight) {
      if (hasMore && !scrollLoading) {
        setOffset(prev => prev + limit);
      }
    }
  }, [hasMore, scrollLoading, limit]);



  useEffect(() => {
    const debouncedHandleScroll = debounce(handleScroll, 200);
    window.addEventListener('scroll', debouncedHandleScroll);
    return () => window.removeEventListener('scroll', debouncedHandleScroll);
  }, [handleScroll]);

  const handleClick = useCallback((symbol) => {
    navigate(`/quote?symbol=${symbol}&action=watch`);
  }, [navigate]);



  if (loading && offset === 0) {
    // Initial loading state
    return (
      <div className="loader-container">
        <div className="loader">
          <div></div><div></div><div></div><div></div>
        </div>
        <h1>Loading Watchlist...</h1>
      </div>
    );
  }



  return (
    <div className="flex flex-col items-center p-6 bg-slate-900 min-h-screen">
      <h1 className="text-3xl font-bold text-blue-100 mb-6">My Watchlist</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full">
        {watchlist.map(stock => (
          <StockCard key={stock.symbol} stock={stock} onClick={handleClick} />
        ))}
      </div>
      {scrollLoading && <div className="loading-spinner"></div>} {/* Show loading spinner only when scrolling */}
      {!hasMore && <p className="text-gray-400 mt-6">No more stocks to load</p>}
      {hasMore && <p className="text-gray-400 mt-6">Scroll down for more</p>}
    </div>
  );
};




const StockCard = React.memo(({ stock, onClick }) => {
  const changeColor = stock.daily_change >= 0 ? 'text-green-400' : 'text-red-400';

  return (
    <div
      className="bg-slate-800 hover:bg-slate-700 p-10 rounded-lg cursor-pointer transition-all"
      onClick={() => onClick(stock.symbol)}
    >
      <h2 className="text-xl font-bold text-white">{stock.symbol}</h2>
      <p className="text-gray-400">{stock.name}</p>
      <p className="text-green-400">Current Price: ${stock.current_price}</p>
      <p className={changeColor}>
        Daily Change: {stock.daily_change.toFixed(2)}%
      </p>
    </div>
  );
});



export default Watchlist;
