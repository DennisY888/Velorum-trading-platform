import axios from "axios";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "./constants";
import {jwtDecode} from "jwt-decode";



// API URL Configuration
const apiUrl = "https://myvelorum.com";



const api = axios.create({
  // baseURL: import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : apiUrl,
  baseURL: apiUrl,
});



// Function to Refresh Token
const refreshToken = async () => {

  const base = import.meta.env.VITE_API_URL

  try {
    const refresh = localStorage.getItem(REFRESH_TOKEN);
    console.log("This is my Refresh Token retrieved in refreshToken():", refresh)

    if (!refresh) {
      throw new Error("Refresh token not found");
    }

    const response = await axios.post(`${base}/api/token/refresh/`, { refresh });

    console.log("This is my Access Token refreshed in refreshToken():", response.data.access)

    localStorage.setItem(ACCESS_TOKEN, response.data.access);
    return response.data.access;
  } catch (error) {
    console.log("Refresh Token Error:", error)
    localStorage.removeItem(ACCESS_TOKEN);
    localStorage.removeItem(REFRESH_TOKEN);
    throw error;
  }
};



// Request Interceptor
api.interceptors.request.use(
  async (config) => {
    try {
      let token = localStorage.getItem(ACCESS_TOKEN);
      console.log("This is my Access Token from request interceptor:", token)
      if (token) {

        const tokenExpiryTime = jwtDecode(token).exp * 1000;
        const currentTime = new Date().getTime();

        if (tokenExpiryTime - currentTime < 5 * 60 * 1000) {
          token = await refreshToken();
          console.log("This should be my Refresh Token from request interceptor retrieved from refreshToken():", token)
        } 

        config.headers.Authorization = `Bearer ${token}`;
      } 
    } catch (error) {
      console.log("Request Interceptor Error:", error)
      throw error;
    }
    return config;
  },

  // this "redirects" error to catch statements used within our code in React to make HTTP requests
  (error) => {
    return Promise.reject(error);
  }
);



// Response Interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },

  async (error) => {
    const originalRequest = error.config;

    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const token = await refreshToken();
        console.log("This should be my Refresh Token from response interceptor retrieved from refreshToken():", token)
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      } catch (error) {
        console.log("Response Interceptor Error:", error)
        localStorage.removeItem(ACCESS_TOKEN);
        localStorage.removeItem(REFRESH_TOKEN);
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);



// Export the API instance
export default api;
