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
    <div className="search-input">
      <input
        type="text"
        value={query}
        onChange={handleInputChange}
        onKeyPress={handleKeyPress}
        placeholder="Enter stock symbol"
      />
      {isDropdownVisible && (
        <div className="autocomplete-dropdown">
          {autoLoading ? (
            <div className="autocomplete-item">
              <p>Loading...</p>
            </div>
          ) : (
            suggestions.map((stock) => (
              <div
                key={stock.symbol}
                onClick={() => handleSelectSuggestion(stock.symbol)}
                className="autocomplete-item"
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
