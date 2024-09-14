import React from "react";

function Autocomplete({ suggestions, onSelect }) {
  return (
    <ul className="autocomplete">
      {suggestions.map((stock) => (
        <li key={stock.symbol} onClick={() => onSelect(stock.symbol)}>
          {stock.symbol} - {stock.name}
        </li>
      ))}
    </ul>
  );
}


export default Autocomplete;
