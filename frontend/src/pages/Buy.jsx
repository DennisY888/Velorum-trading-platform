import React from 'react';
import SearchInput from "../components/SearchInput";
import { useNavigate } from 'react-router-dom';

const Buy = () => {
  const navigate = useNavigate();

  const handleSymbolSelected = (symbol) => {
    navigate(`/quote?symbol=${symbol}&action=buy`);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="flex flex-col items-center">
        <h1 className="text-5xl font-bold text-blue-100 mb-10" style={{ marginTop: '-150px' }}>Find Your Desired Stock</h1>
        <SearchInput onSymbolSelected={handleSymbolSelected} isSellPage={false} />
      </div>
    </div>
  );
};

export default React.memo(Buy);