import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from "../api";

const RemoveFromWatchlistButton = ({ symbol }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

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
  }, [symbol, navigate]);

  return (
    <div className="action-section">
      <button 
        onClick={handleRemoveFromWatchlist} 
        className="w-full py-4 text-lg font-semibold bg-gradient-to-r from-red-400 to-red-600 text-white rounded-lg shadow-lg hover:bg-red-500 transition-all duration-300 ease-in-out transform hover:scale-105"
        disabled={loading}
      >
        {loading ? "Removing..." : "Remove from Watchlist"}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default RemoveFromWatchlistButton;
