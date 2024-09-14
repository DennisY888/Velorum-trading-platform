import React, { useState, useEffect, useCallback } from 'react';
import api from "../api";
import { useNavigate, useSearchParams } from 'react-router-dom';
import NotFound from './NotFound'; 
import RemoveFromWatchlistButton from '../components/RemoveFromWatchlistButton';
import "../styles/Quote.css";

const Quote = () => {
  const [searchParams] = useSearchParams();
  const symbol = searchParams.get('symbol');
  const action = searchParams.get('action'); // "buy" or "sell"
  const [stockData, setStockData] = useState(null);
  const [shares, setShares] = useState('');
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);  // To handle errors
  const [initialLoad, setInitialLoad] = useState(true);



  const fetchStockData = useCallback(async () => {
    if (initialLoad) {
      setLoading(true);
    }
    try {
      let response;
      if (action === 'sell') {
        response = await api.get(`/api/search-owned-stocks/?q=${symbol}`);
      } else {
        response = await api.get(`/api/quote/${symbol}/`);
      }

      if (response.data && response.data.length > 0) {
        setStockData(response.data[0]);
      } else if (response.data && (action === 'buy' || action === 'watch')) {
        setStockData(response.data);
      } else {
        setStockData(null);
      }

      setInitialLoad(false);
    } catch (error) {
      console.error('Error fetching stock data:', error);
      setStockData(null);
    } finally {
      setLoading(false);
    }
  }, [symbol, action, initialLoad]);



  useEffect(() => {
    fetchStockData();

    const intervalId = setInterval(() => {
      fetchStockData();
    }, 40000);

    return () => clearInterval(intervalId);
  }, [fetchStockData]);



  const handleSharesChange = useCallback((e) => {
    setShares(e.target.value);
  }, []);



  const handleAction = useCallback(async () => {
    const endpoint = action === 'buy' ? '/api/portfolio/buy/' : '/api/portfolio/sell/';
    setLoading(true);
    setError(null);  // Reset error before starting
    try {
      await api.post(endpoint, { symbol, shares });
      navigate('/');
    } catch (error) {
      // Assuming backend sends a status code 400 for insufficient funds or not enough shares
      if (error.response && error.response.status === 400) {
        if (action === 'buy') {
          setError('Insufficient funds to complete the purchase.');
        } else if (action === 'sell') {
          setError('Not enough shares to complete the sale.');
        }
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [symbol, shares, action, navigate]);



  const handleAddToWatchlist = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post("/api/watchlist/add_to_watchlist/", { symbol });
      alert("Stock added to watchlist!");
      navigate('/watchlist');
    } catch (error) {
      console.error("Error adding stock to watchlist:", error);
      setError("Failed to add stock to watchlist. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [symbol]);



  if (loading && initialLoad) {
    return (
      <div className="loader-container">
        <div className="loader">
          <div></div><div></div><div></div><div></div>
        </div>
        <h1>Loading Stock Data...</h1>
      </div>
    );
  }



  if (!stockData) {
    return <NotFound />;
  }


  
  return (
    <div className="quote-page text-slate-100 p-6 md:p-12">
      <h1 className="text-6xl font-extrabold mb-6 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-green-400">
        {stockData.symbol} - {stockData.name}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 text-lg leading-6">
        <p className="font-semibold">Current Price: <span className="text-blue-300">${stockData.current_price}</span></p>
        <p className="font-semibold">Opening Price: <span className="text-blue-300">${stockData.opening_price}</span></p>
        <p className="font-semibold">Previous Close: <span className="text-blue-300">${stockData.previous_close}</span></p>
        <p className="font-semibold">High Price: <span className="text-blue-300">${stockData.high_price}</span></p>
        <p className="font-semibold">Low Price: <span className="text-blue-300">${stockData.low_price}</span></p>
        <p className="font-semibold">10 Day Avg Volume: <span className="text-blue-300">{stockData.ten_day_avg_volume}M</span></p>
        <p className="font-semibold">3 Month Avg Volume: <span className="text-blue-300">{stockData.three_month_avg_volume}M</span></p>
        <p className="font-semibold">Market Cap: <span className="text-blue-300">{stockData.market_cap}M</span></p>
        <p className="font-semibold">P/E Ratio: <span className="text-blue-300">{stockData.pe_ratio}</span></p>
        <p className="font-semibold">Annual Dividend Yield: <span className="text-blue-300">{stockData.annual_dividend_yield}%</span></p>
        <p className="font-semibold">52 Week High: <span className="text-blue-300">${stockData['52_week_high']}</span></p>
        <p className="font-semibold">52 Week Low: <span className="text-blue-300">${stockData['52_week_low']}</span></p>
        <p className="font-semibold">Beta: <span className="text-blue-300">{stockData.beta}</span></p>
        <p className="font-semibold">Exchange: <span className="text-blue-300">{stockData.exchange}</span></p>
      </div>

      {action !== 'watch' && (
        <div className="action-section space-y-6">
          <input
            type="number"
            placeholder="Number of shares"
            value={shares}
            onChange={handleSharesChange}
            className="w-full p-4 text-lg rounded-full bg-slate-800 text-blue-100 placeholder-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-600 caret-blue-200 shadow-lg"
          />
          <button 
            onClick={handleAction} 
            className="w-full py-4 text-lg font-semibold bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-lg shadow-lg hover:bg-blue-700 transition-all duration-300 ease-in-out transform hover:scale-105"
          >
            {action === 'buy' ? 'Buy' : 'Sell'}
          </button>
          <button 
            onClick={handleAddToWatchlist} 
            className="w-full py-4 text-lg font-semibold bg-gradient-to-r from-yellow-400 to-yellow-600 text-white rounded-lg shadow-lg hover:bg-yellow-500 transition-all duration-300 ease-in-out transform hover:scale-105"
          >
            Add to Watchlist
          </button>
        </div>
      )}

      {action === 'watch' && <RemoveFromWatchlistButton symbol={symbol} />}

      {error && (
        <div className="mt-6">
          <h1 className="text-red-500 text-2xl font-bold text-center">{error}</h1>
        </div>
      )}
    </div>
  );
};

export default React.memo(Quote);
