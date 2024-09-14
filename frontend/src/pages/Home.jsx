import React, { useState, useEffect, useCallback } from "react";
import api from "../api";
import "../styles/Home.css";
import { Line, Pie } from "react-chartjs-2";  // Import Line and Pie components from react-chartjs-2
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
} from "chart.js";  // Import necessary chart types from Chart.js



// Register the required chart components with Chart.js
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);

function Home() {
  const [portfolio, setPortfolio] = useState([]);
  const [cash, setCash] = useState(0);
  const [username, setUsername] = useState("");
  const [grandTotal, setGrandTotal] = useState(0);
  const [portfolioHistory, setPortfolioHistory] = useState([]);  // State for portfolio history (line chart)
  const [portfolioBreakdown, setPortfolioBreakdown] = useState([]);  // State for portfolio breakdown (pie chart)
  const [portfolioCash, setPortfolioCash] = useState([])
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);



  // Function to fetch the user's portfolio summary (existing logic)
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



  // Function to fetch portfolio history for the line chart
  const fetchPortfolioHistory = useCallback(() => {
    api.get("/api/portfolio-history/")
      .then((response) => {
        setPortfolioHistory(response.data);
        console.log(response.data)
      })
      .catch((error) => {
        console.error("Error fetching portfolio history:", error);
      });
  }, []);



  // Function to fetch portfolio breakdown for the pie chart
  const fetchPortfolioBreakdown = useCallback(() => {
    api.get("/api/portfolio-breakdown/")
      .then((response) => {
        setPortfolioBreakdown(response.data.portfolio);
        setPortfolioCash(response.data.cash);
        console.log(response.data)
      })
      .catch((error) => {
        console.error("Error fetching portfolio breakdown:", error);
      });
  }, []);



  // Fetch portfolio summary and set a 1-minute interval (existing logic)
  useEffect(() => {
    fetchPortfolio();
    const intervalId = setInterval(fetchPortfolio, 40000);
    return () => clearInterval(intervalId);
  }, [fetchPortfolio]);



  // Fetch portfolio history and breakdown when the component loads
  useEffect(() => {
    fetchPortfolioHistory();
    fetchPortfolioBreakdown();
  }, [fetchPortfolioHistory, fetchPortfolioBreakdown]);



  // Define data and options for the Portfolio Value Over Time chart (Line Chart)
  const lineChartData = {
    labels: portfolioHistory.map((entry) => entry.date), // X-axis (dates)
    datasets: [
      {
        label: "Portfolio Value",
        data: portfolioHistory.map((entry) => entry.total_value), // Y-axis (portfolio values)
        borderColor: "#38bdf8", // Aqua blue line color
        backgroundColor: "rgba(56, 189, 248, 0.2)", // Light blue fill under the line
        fill: true,
        tension: 0.3,
      },
    ],
  };



  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function (tooltipItem) {
            return `Total Value: $${tooltipItem.formattedValue}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#cbd5e1", // Text color for X-axis
        },
        grid: {
          color: "rgba(255, 255, 255, 0.1)", // Grid color for X-axis
        },
      },
      y: {
        ticks: {
          color: "#cbd5e1", // Text color for Y-axis
        },
        grid: {
          color: "rgba(255, 255, 255, 0.1)", // Grid color for Y-axis
        },
      },
    },
  };



  // Define data and options for the Stock Performance Breakdown chart (Pie Chart)
  const pieChartData = {
    labels: [
      ...portfolioBreakdown.map((stock) => stock.symbol),  // Stock symbols
      "Cash"  // Add cash slice label
    ],
    datasets: [
      {
        data: [
          ...portfolioBreakdown.map((stock) => stock.current_value),  // Stock values
          portfolioCash.value  // Add cash slice value
        ],
        backgroundColor: [
          ...portfolioBreakdown.map((stock) => stock.color),  // Stock colors
          portfolioCash.color  // Add cash slice color
        ],
        borderWidth: 0,
      },
    ],
  };
  



  const pieChartOptions = {
    plugins: {
      tooltip: {
        callbacks: {
          label: function (tooltipItem) {
            const stock = portfolioBreakdown[tooltipItem.dataIndex];
            // Handle both stock and cash tooltips
            if (tooltipItem.dataIndex === portfolioBreakdown.length) {
              return `Cash: $${portfolioCash.value} (${portfolioCash.percent}%)`;  // Cash slice
            }
            return `${stock.symbol}: $${stock.current_value} (${stock.percent}%)`;  // Stock slice
          },
        },
      },
    },
  };



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


      {/* Add the Portfolio Value Over Time (Line Chart) */}
      <div className="charts-container">
        {/* Add the Portfolio Value Over Time (Line Chart) */}
        <div className="chart-container chart-left">
          <h2>Portfolio Value Over Time {"(Updated Daily at 5:00pm ET)"}</h2>
          <Line data={lineChartData} options={lineChartOptions} />
        </div>

        {/* Add the Stock Performance Breakdown (Pie Chart) */}
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
