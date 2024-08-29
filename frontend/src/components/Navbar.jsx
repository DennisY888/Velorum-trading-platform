import React from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/Navbar.css";

function Navbar() {
  const navigate = useNavigate();
  const isLoggedIn = !!localStorage.getItem("access"); // Assuming you store access tokens in localStorage

  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <ul>
        {isLoggedIn ? (
          <>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/buy">Search/Buy</Link></li>
            <li><Link to="/sell">Sell</Link></li>
            <li><Link to="/history">History</Link></li>
            <li><Link to="/leaderboard">Leaderboard</Link></li>
            <li><Link to="/watchlist">Watchlist</Link></li>
            <li><Link to="/logout">Logout</Link></li>
          </>
        ) : (
          <>
            <li><Link to="/login">Login</Link></li>
            <li><Link to="/register">Register</Link></li>
          </>
        )}
      </ul>
    </nav>
  );
}

export default Navbar;
