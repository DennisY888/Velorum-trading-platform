import react from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Home from "./pages/Home"
import NotFound from "./pages/NotFound"

import History from "./pages/History"
import Leaderboard from "./pages/Leaderboard"
import Buy from "./pages/Buy"
import Sell from "./pages/Sell"
import Quote from "./pages/Quote"
import Watchlist from "./pages/Watchlist"
import Navbar from "./components/Navbar";

import ProtectedRoute from "./components/ProtectedRoute"


// small, custom components, no need to be in pages folder
function Logout() {
  // clear our two tokens, user would need to login again
  localStorage.clear()
  return <Navigate to="/login" />
}


// clear the local storage first so that we don't end up submitting access tokens to register route, could cause errors
function RegisterAndLogout() {
  // make sure we don't have any old access tokens lingering around
  localStorage.clear()
  return <Register />
}




// write the overall navigation (how to go between different pages) using React Router DOM

function App() {

  return (
    <BrowserRouter>

      {/* Navbar provides a visual way for user to trigger navigation */}
      <Navbar />


      {/* All these routes are responsible to render the appropriate component when navigation triggered */}
      <Routes>
        <Route
          path="/"
          element={<ProtectedRoute><Home /></ProtectedRoute>}
        />
        <Route
          path="/buy"
          element={<ProtectedRoute><Buy /></ProtectedRoute>}
        />
        <Route
          path="/sell"
          element={<ProtectedRoute><Sell /></ProtectedRoute>}
        />
        <Route
          path="/history"
          element={<ProtectedRoute><History /></ProtectedRoute>}
        />
        <Route
          path="/leaderboard"
          element={<ProtectedRoute><Leaderboard /></ProtectedRoute>}
        />
        <Route
          path="/watchlist"
          element={<ProtectedRoute><Watchlist /></ProtectedRoute>}
        />
        <Route
          path="/quote"
          element={<ProtectedRoute><Quote /></ProtectedRoute>}
        />
        <Route 
          path="/logout" 
          element={<ProtectedRoute><Logout /></ProtectedRoute>} 
        />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<RegisterAndLogout />} />
        {/* any other route would be a 404 page */}
        <Route path="*" element={<NotFound />}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
