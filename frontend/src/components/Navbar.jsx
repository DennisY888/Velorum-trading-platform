import React from "react";
import { Link, useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();
  const isLoggedIn = !!localStorage.getItem("access"); // Assuming you store access tokens in localStorage

  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  return (
    <nav className="bg-gradient-to-l from-slate-800 to-slate-900 p-4 shadow-lg">
      <ul className="list-none m-0 p-0 flex justify-around">
        {isLoggedIn ? (
          <>
            <li className="inline font-semibold">
              <Link to="/" className="nav-link">
                Home
              </Link>
            </li>
            <li className="inline font-semibold">
              <Link to="/buy" className="nav-link">
                Search/Buy
              </Link>
            </li>
            <li className="inline font-semibold">
              <Link to="/sell" className="nav-link">
                Sell
              </Link>
            </li>
            <li className="inline font-semibold">
              <Link to="/history" className="nav-link">
                History
              </Link>
            </li>
            <li className="inline font-semibold">
              <Link to="/leaderboard" className="nav-link">
                Leaderboard
              </Link>
            </li>
            <li className="inline font-semibold">
              <Link to="/watchlist" className="nav-link">
                Watchlist
              </Link>
            </li>
            <li className="inline font-semibold">
              <Link to="/logout" className="nav-link">
                Logout
              </Link>
            </li>
          </>
        ) : (
          <>
            <li className="inline font-semibold">
              <Link to="/login" className="nav-link">
                Login
              </Link>
            </li>
            <li className="inline font-semibold">
              <Link to="/register" className="nav-link">
                Register
              </Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
}

export default Navbar;
