import React from 'react';
import SearchInput from "../components/SearchInput";
import { useNavigate } from 'react-router-dom';

const Buy = () => {
  const navigate = useNavigate();

  const handleSymbolSelected = (symbol) => {
    navigate(`/quote?symbol=${symbol}&action=buy`);
  };

  return (
    <div className="buy-page">
      <h1>Search Up Any Stock</h1>
      <SearchInput onSymbolSelected={handleSymbolSelected} isSellPage={false} />
    </div>
  );
};

export default React.memo(Buy);
