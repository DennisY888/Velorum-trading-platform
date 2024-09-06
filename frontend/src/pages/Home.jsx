import React, { useState, useEffect, useCallback } from "react";
import api from "../api";
import "../styles/Home.css";

function Home() {
  const [portfolio, setPortfolio] = useState([]);
  const [cash, setCash] = useState(0);
  const [username, setUsername] = useState("");
  const [grandTotal, setGrandTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);

  const fetchPortfolio = useCallback(() => {
    if (initialLoad) {
      setLoading(true);
    }

    api.get("/api/index/")
      .then((response) => {
        setPortfolio(response.data.portfolio);
        setUsername(response.data.username);
        setCash(response.data.cash);
        setGrandTotal(response.data.grand_total);
        setInitialLoad(false);
      })
      .catch((error) => {
        console.error("Error fetching portfolio data:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [initialLoad]);

  useEffect(() => {
    fetchPortfolio();
    const intervalId = setInterval(fetchPortfolio, 60000);
    return () => clearInterval(intervalId);
  }, [fetchPortfolio]);

  if (loading && initialLoad) {
    return (
      <div className="loader-container">
        <div className="loader">
          <div></div><div></div><div></div><div></div>
        </div>
        <h1>Loading Portfolio...</h1>
      </div>
    );
  }



  return (
    <div className="home">
      <div className="welcome-section">
        <div className="welcome-message">
          <h1>Welcome, {username}</h1>
        </div>
      </div>

      <div className="portfolio-summary">
        <h1 className="portfolio-title">Portfolio Overview</h1>
        <p>Total Portfolio Value: <span>${grandTotal.toFixed(2)}</span></p>
        <p>Current Cash: <span>${cash.toFixed(2)}</span></p>
      </div>

      {portfolio.length === 0 ? (
        <h1 className="no-holdings">No Stock Holdings</h1>
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
                <td className={stock.daily_change >= 0 ? "glow-green" : "glow-red"}>
                  {stock.daily_change.toFixed(2)}%
                </td>

              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Home;
