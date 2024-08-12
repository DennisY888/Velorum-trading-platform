import react from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Home from "./pages/Home"
import NotFound from "./pages/NotFound"
import ProtectedRoute from "./components/ProtectedRoute"


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
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route path="/register" element={<RegisterAndLogout />} />
        {/* any other route would be a 404 page */}
        <Route path="*" element={<NotFound />}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
