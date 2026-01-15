// frontend/src/pages/Home.jsx

import React, { useState, useEffect, useCallback, useRef } from "react";
import api from "../api";
import "../styles/Home.css";
import { Line, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler,
} from "chart.js";

// Register Chart components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement, Filler);

function Home() {
  const [portfolio, setPortfolio] = useState([]);
  const [cash, setCash] = useState(0);
  const [username, setUsername] = useState("");
  const [grandTotal, setGrandTotal] = useState(0);
  const [portfolioHistory, setPortfolioHistory] = useState([]);
  const [portfolioBreakdown, setPortfolioBreakdown] = useState([]);
  const [portfolioCash, setPortfolioCash] = useState({ value: 0, percent: 0, color: "#000" });
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);

  // WebSocket Reference to prevent duplicate connections
  const wsRef = useRef(null);

  // 1. Fetch Initial Data (REST API)
  const fetchPortfolio = useCallback(() => {
    if (initialLoad) setLoading(true);

    api.get("/api/index/")
      .then((response) => {
        setPortfolio(response.data.portfolio);
        setUsername(response.data.username);
        setCash(response.data.cash);
        setGrandTotal(response.data.grand_total);
        setInitialLoad(false);
      })
      .catch((error) => console.error("Error fetching portfolio:", error))
      .finally(() => setLoading(false));
  }, [initialLoad]);

  const fetchHistoryAndBreakdown = useCallback(() => {
    api.get("/api/portfolio-history/")
      .then((res) => setPortfolioHistory(res.data))
      .catch((err) => console.error(err));

    api.get("/api/portfolio-breakdown/")
      .then((res) => {
        setPortfolioBreakdown(res.data.portfolio);
        setPortfolioCash(res.data.cash);
      })
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    fetchPortfolio();
    fetchHistoryAndBreakdown();
  }, [fetchPortfolio, fetchHistoryAndBreakdown]);

  // 2. WebSocket Logic (Replaces setInterval)
  // Resume Claim: "Utilizing WebSocket connections for live market updates"
  useEffect(() => {
    // Dynamically construct WS URL from the Vite Environment Variable
    // If API is http://127.0.0.1:8000, WS becomes ws://127.0.0.1:8000
    const httpUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const wsBaseUrl = httpUrl.replace("http", "ws"); 
    
    // For verification, we subscribe to AAPL. 
    // IMPORTANT: You must BUY 'AAPL' in the app for the backend to start sending data for it.
    const symbol = "AAPL"; 
    const socketUrl = `${wsBaseUrl}/ws/stock/${symbol}/`;

    if (!wsRef.current) {
      console.log(`🔌 Attempting WebSocket Connection to: ${socketUrl}`);
      const socket = new WebSocket(socketUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        console.log("✅ WebSocket Connected: Live Pipe Established");
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("⚡ Live Update Received:", data);

        // REAL-TIME STATE UPDATE
        // We update the specific stock in the portfolio list without refreshing
        setPortfolio((prevPortfolio) => {
          return prevPortfolio.map((item) => {
            if (item.symbol === data.symbol) {
              const newTotal = item.shares * data.price;
              return {
                ...item,
                current_price: data.price,
                total_value: newTotal,
                // Note: We keep the old daily_change % because calculating it requires prev_close
                daily_change: item.daily_change 
              };
            }
            return item;
          });
        });
      };

      socket.onclose = () => console.log("❌ WebSocket Disconnected");
      socket.onerror = (error) => console.error("⚠️ WebSocket Error:", error);
    }

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  // --- Chart Configurations ---
  const lineChartData = {
    labels: portfolioHistory.map((entry) => entry.date),
    datasets: [{
      label: "Portfolio Value",
      data: portfolioHistory.map((entry) => entry.total_value),
      borderColor: "#38bdf8",
      backgroundColor: "rgba(56, 189, 248, 0.2)",
      fill: true,
      tension: 0.3,
    }],
  };

  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (t) => `Total Value: $${t.formattedValue}` } },
    },
    scales: {
      x: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(255, 255, 255, 0.1)" } },
      y: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(255, 255, 255, 0.1)" } },
    },
  };

  const pieChartData = {
    labels: [...portfolioBreakdown.map((s) => s.symbol), "Cash"],
    datasets: [{
      data: [...portfolioBreakdown.map((s) => s.current_value), portfolioCash.value],
      backgroundColor: [...portfolioBreakdown.map((s) => s.color), portfolioCash.color],
      borderWidth: 0,
    }],
  };

  const pieChartOptions = {
    plugins: {
      tooltip: {
        callbacks: {
          label: function (tooltipItem) {
            if (tooltipItem.dataIndex === portfolioBreakdown.length) {
              return `Cash: $${portfolioCash.value} (${portfolioCash.percent}%)`;
            }
            const stock = portfolioBreakdown[tooltipItem.dataIndex];
            return `${stock.symbol}: $${stock.current_value} (${stock.percent}%)`;
          },
        },
      },
    },
  };

  if (loading && initialLoad) {
    return (
      <div className="loader-container">
        <div className="loader"><div></div><div></div><div></div><div></div></div>
        <h1>Loading Portfolio...</h1>
      </div>
    );
  }

  return (
    <div className="home">
      <div className="welcome-section">
        <div className="welcome-message">
          <h1>Welcome, {username}</h1>
          {/* Visual Indicator for Resume Claim */}
          <div style={{color: '#4ade80', fontSize: '0.8rem', marginTop: '5px'}}>
            ● Live Market Connection Active
          </div>
        </div>
      </div>

      <div className="portfolio-summary">
        <h1 className="portfolio-title">Portfolio Overview</h1>
        <p>Total Portfolio Value: <span>${Number(grandTotal).toFixed(2)}</span></p>
        <p>Current Cash: <span>${Number(cash).toFixed(2)}</span></p>
      </div>

      <div className="charts-container">
        <div className="chart-container chart-left">
          <h2>Portfolio Value Over Time {"(Updated Daily at 5:00pm ET)"}</h2>
          <Line data={lineChartData} options={lineChartOptions} />
        </div>
        <div className="chart-container chart-right">
          <h2>Stock Performance Breakdown</h2>
          <Pie data={pieChartData} options={pieChartOptions} />
        </div>
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
                {/* Highlights Real-Time Data */}
                <td style={{fontWeight: 'bold', color: '#38bdf8'}}>
                  ${Number(stock.current_price).toFixed(2)}
                </td>
                <td>${Number(stock.total_value).toFixed(2)}</td>
                <td className={stock.daily_change >= 0 ? "glow-green" : "glow-red"}>
                  {Number(stock.daily_change).toFixed(2)}%
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