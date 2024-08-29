import React, { useState, useEffect, useCallback } from "react";
import api from "../api";

function Home() {
  const [portfolio, setPortfolio] = useState([]);
  const [cash, setCash] = useState(0);
  const [grandTotal, setGrandTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);  // New state to track initial load

  // useCallback to memoize the fetch function and prevent unnecessary re-creations
  const fetchPortfolio = useCallback(() => {
    if (initialLoad) {
      setLoading(true);
    }

    api.get("/api/index/")
      .then((response) => {
        setPortfolio(response.data.portfolio);
        setCash(response.data.cash);
        setGrandTotal(response.data.grand_total);
        setInitialLoad(false);  // Mark initial load as complete
      })
      .catch((error) => {
        console.error("Error fetching portfolio data:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [initialLoad]);  // Include initialLoad as a dependency

  useEffect(() => {
    // Initial fetch when the component mounts
    fetchPortfolio();

    // Set up an interval to fetch data every minute for real-time updates
    const intervalId = setInterval(fetchPortfolio, 60000);

    // Cleanup interval on component unmount
    return () => clearInterval(intervalId);
  }, [fetchPortfolio]); // Dependency ensures this effect runs only when fetchPortfolio changes

  if (loading && initialLoad) {  // Only show loading during the initial load
    return <h1>Loading...</h1>;
  }

  return (
    <div className="home">
      <div className="portfolio-summary">
        <h1>Portfolio Overview</h1>
        <p>Total Portfolio Value: ${grandTotal.toFixed(2)}</p>
        <p>Current Cash: ${cash.toFixed(2)}</p>
      </div>

      {portfolio.length === 0 ? (
        <h1>No Stock Holdings</h1>
      ) : (
        <table className="portfolio-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Shares</th>
              <th>Current Price</th>
              <th>Total Value</th>
              <th>Percent Change</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.map((stock) => (
              <tr key={stock.symbol}>
                <td>{stock.symbol}</td>
                <td>{stock.shares}</td>
                <td>${stock.current_price.toFixed(2)}</td>
                <td>${stock.total_value.toFixed(2)}</td>
                <td>{stock.daily_change.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Home;
