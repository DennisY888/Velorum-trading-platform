import React from 'react';
import SearchInput from "../components/SearchInput";
import { useNavigate } from 'react-router-dom';

const Sell = () => {
  const navigate = useNavigate();

  const handleSymbolSelected = (symbol) => {
    navigate(`/quote?symbol=${symbol}&action=sell`);
  };

  return (
    <div className="sell-page">
      <h1>Sell Any Stock You Own</h1>
      <SearchInput onSymbolSelected={handleSymbolSelected} isSellPage={true} />
    </div>
  );
};

export default React.memo(Sell);
