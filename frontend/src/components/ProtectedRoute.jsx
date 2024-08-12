// a wrapper for any protected route
// we need to have an authorization token before accessing this route


import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import api from "../api";
import { REFRESH_TOKEN, ACCESS_TOKEN } from "../constants";
import { useState, useEffect } from "react";



// children is the component route that will be wrapped
function ProtectedRoute({ children }) {
    const [isAuthorized, setIsAuthorized] = useState(null);


    useEffect(() => {
        // if there are error we can catch it and just set isAuthorized to false
        auth().catch(() => setIsAuthorized(false))
    }, [])


    // refresh the access token for us automatically
    const refreshToken = async () => {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN);

        try {
            // send a request to backend with refresh token
            // our api object automatically handles the base url for us (the front half of the url)
            const res = await api.post("/api/token/refresh/", {
                refresh: refreshToken,
            });

            if (res.status === 200) {
                localStorage.setItem(ACCESS_TOKEN, res.data.access)
                setIsAuthorized(true)
            } else {
                setIsAuthorized(false)
            }
        } catch (error) {
            console.log(error);
            setIsAuthorized(false);
        }
    };


    // checks if the user has a token, 
    // if the user has one, check if we need to refresh their access token
    // if we cannot refresh the token, set isAuthorized to false
    const auth = async () => {
        const token = localStorage.getItem(ACCESS_TOKEN);
        if (!token) {
            setIsAuthorized(false);
            return;
        }

        // gives us the value and expiration date of the token
        const decoded = jwtDecode(token);

        const tokenExpiration = decoded.exp;

        // get date in seconds not milliseconds
        const now = Date.now() / 1000;

        if (tokenExpiration < now) {
            await refreshToken();
        } else {
            setIsAuthorized(true);
        }
    };


    // while we are checking if user is authorized
    if (isAuthorized === null) {
        return <div>Loading...</div>;
    }


    // if user is not authorized, redirect them to login page, else display the children page
    return isAuthorized ? children : <Navigate to="/login" />;
}

export default ProtectedRoute;


