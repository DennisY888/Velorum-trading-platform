import React, { useState, useEffect, useCallback } from 'react';
import api from "../api";
import debounce from 'lodash.debounce';

const SearchInput = ({ onSymbolSelected, isSellPage }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isDropdownVisible, setDropdownVisible] = useState(false);
  const [autoLoading, setAutoLoading] = useState(false);


  const handleInputChange = useCallback((e) => {
    const value = e.target.value.toUpperCase();
    setQuery(value);
    if (isSellPage) {
      setDropdownVisible(true)
    }
  }, []);



  // Debounced function to fetch autocomplete suggestions for the Sell page
  const fetchSuggestions = useCallback(
    debounce(async (query) => {
      if (query && isSellPage) {
        setAutoLoading(true);
        try {
          const response = await api.get(`/api/search-owned-stocks/?q=${query}`);
          setSuggestions(response.data);
        } catch (error) {
          console.error('Error fetching autocomplete suggestions:', error);
        } finally {
          setAutoLoading(false);
        }
      } else {
        setSuggestions([]);
        setDropdownVisible(false);
        setAutoLoading(false);
      }
    }, 300),
    [isSellPage]
  );



  useEffect(() => {
    if (isSellPage) {
      fetchSuggestions(query);
    }
  }, [query, fetchSuggestions, isSellPage]);



  const handleSelectSuggestion = useCallback((symbol) => {
    setQuery(symbol);
    setDropdownVisible(false);
    onSymbolSelected(symbol);
  }, [onSymbolSelected]);



  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && query) {
      onSymbolSelected(query);
    }
  }, [query, onSymbolSelected]);



  return (
      <div className='w-full max-w-lg relative' >

          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Enter stock symbol"
            className="w-full p-4 text-xl rounded-full bg-slate-800 text-blue-100 placeholder-blue-400 focus:outline-none focus:ring-2 focus:ring-slate-600 caret-blue-200"
            style={{ 
              textShadow: '0 0 8px rgba(255, 255, 255, 0.7)', // White glow effect
              animation: 'glow 1s infinite alternate' // Blinking glow effect
            }}
          />

      {isDropdownVisible && (
        <div className="absolute w-full mt-1 rounded-lg bg-gradient-to-r from-slate-800 to-slate-900 shadow-lg overflow-hidden z-10">
          {autoLoading ? (
            <div className="p-4 hover:bg-slate-700 text-blue-100 cursor-pointer">
              <p>Loading...</p>
            </div>
          ) : (
            suggestions
              .filter((stock) => stock && stock.symbol)  // Filter out null or invalid stocks
              .map((stock) => (
                <div
                  key={stock.symbol}
                  onClick={() => handleSelectSuggestion(stock.symbol)}
                  className="p-4 hover:bg-slate-700 text-blue-100 cursor-pointer"
                >
                  <p>{stock.symbol} - {stock.name}</p>
                </div>
              ))
          )}

        </div>
      )}

    </div>
  );
};



export default React.memo(SearchInput);
