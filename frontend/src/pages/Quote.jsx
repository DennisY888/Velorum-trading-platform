import React, { useState, useEffect, useCallback } from 'react';
import api from "../api";
import { useNavigate, useSearchParams } from 'react-router-dom';
import NotFound from './NotFound'; // Assuming NotFound is already implemented

const Quote = () => {
  const [searchParams] = useSearchParams();
  const symbol = searchParams.get('symbol');
  const action = searchParams.get('action'); // "buy" or "sell"
  const [stockData, setStockData] = useState(null);
  const [shares, setShares] = useState('');
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);  // To handle errors



  const fetchStockData = useCallback(async () => {
    setLoading(true);
    try {
      let response;
      if (action === 'sell') {
        // Fetch from user's owned stocks for Sell page
        response = await api.get(`/api/search-owned-stocks/?q=${symbol}`);
      } else {
        // Fetch from the entire stock market for Buy page
        response = await api.get(`/api/quote/${symbol}/`);
      }


      if (response.data && response.data.length > 0) {
        // For Sell page, the response might return an array of matching stocks
        setStockData(response.data[0]); // Assuming we're interested in the first match
      } else if (response.data && (action === 'buy' || action === 'watch')) {
        // For Buy page, if we get a valid response with data, set it
        setStockData(response.data);
      } else {
        // If no valid data, treat it as not found
        setStockData(null);
      }
    } catch (error) {
      console.error('Error fetching stock data:', error);
      setStockData(null); // In case of an error, treat it as not found
    } finally {
      setLoading(false);
    }
  }, [symbol, action]);




  useEffect(() => {
    fetchStockData();

    const intervalId = setInterval(() => {
      fetchStockData();
    }, 60000); // Refresh every 60 seconds

    return () => clearInterval(intervalId);
  }, [fetchStockData]);



  const handleSharesChange = useCallback((e) => {
    setShares(e.target.value);
  }, []);



  const handleAction = useCallback(async () => {
    const endpoint = action === 'buy' ? '/api/portfolio/buy/' : '/api/portfolio/sell/';
    setLoading(true);
    try {
      await api.post(endpoint, { symbol, shares });
      navigate('/');
    } catch (error) {
      console.error(`Error performing ${action}:`, error);
    } finally {
      setLoading(false);
    }
  }, [symbol, shares, action, navigate]);



  // New function to handle adding to watchlist
  const handleAddToWatchlist = useCallback(async () => {
    setLoading(true);
    setError(null);  // Reset error state
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



  const handleRemoveFromWatchlist = useCallback(async () => {
    setLoading(true);
    setError(null);  // Reset error state
    try {
      await api.delete("/api/watchlist/remove_from_watchlist/", { data: {symbol} });
      alert("Stock removed from watchlist!");
      navigate('/watchlist');
    } catch (error) {
      console.error("Error removing stock from watchlist:", error);
      setError("Failed to remove stock from watchlist. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [symbol]);




  if (loading) {
    return <h1>Loading...</h1>;
  }


  if (!stockData) {
    return <NotFound />;
  }


  return (
    <div className="quote-page">
      <h1>{stockData.symbol} - {stockData.name}</h1>
      <p>Current Price: ${stockData.current_price}</p>
      <p>Opening Price: ${stockData.opening_price}</p>
      <p>Previous Close: ${stockData.previous_close}</p>
      <p>High Price: ${stockData.high_price}</p>
      <p>Low Price: ${stockData.low_price}</p>
      <p>10 Day Avg Volume: {stockData.ten_day_avg_volume}M</p>
      <p>3 Month Avg Volume: {stockData.three_month_avg_volume}M</p>
      <p>Market Cap: {stockData.market_cap}M</p>
      <p>P/E Ratio: {stockData.pe_ratio}</p>
      <p>Annual Dividend Yield: {stockData.annual_dividend_yield}%</p>
      <p>52 Week High: ${stockData['52_week_high']}</p>
      <p>52 Week Low: ${stockData['52_week_low']}</p>
      <p>Beta: {stockData.beta}</p>
      <p>Exchange: {stockData.exchange}</p>
      
      
      {action !== 'watch' && (
        <div className="action-section">
          <input
            type="number"
            placeholder="Number of shares"
            value={shares}
            onChange={handleSharesChange}
          />
          <button onClick={handleAction}>{action === 'buy' ? 'Buy' : 'Sell'}</button>
          <button onClick={handleAddToWatchlist} style={{ marginTop: '10px' }}>
            Add to Watchlist
          </button>
        </div>
      )}


      {action === 'watch' && (
        <div className="action-section">
          <button onClick={handleRemoveFromWatchlist} style={{ marginTop: '10px' }}>
            Remove from Watchlist
          </button>
        </div>
      )}

      {/* Display any error messages */}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default React.memo(Quote);
