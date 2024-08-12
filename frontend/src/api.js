// this is an interceptor, automatically intercepts any requests we are going to send and add correct headers
// we will use axios, a clean way to send network requests
// in our case, everytime we send request our access token will be automatically added to the request


import axios from "axios";
import { ACCESS_TOKEN } from "./constants";

const apiUrl = "/choreo-apis/awbo/backend/rest-api-be2/v1.0";



const api = axios.create({
  // allows us to import any variable specified in the .env file (environment variable file)
  baseURL: import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : apiUrl,
});



// takes a function as argument
// telling Axios to run some code right before every request is sent out
api.interceptors.request.use(
  
  // look into our local storage to see if there is an access token
  // if there is we add that token as autorization header to our request

  // config contains all the details about the request, such as the method (GET, POST, etc.), the URL, headers,
  (config) => {
    const token = localStorage.getItem(ACCESS_TOKEN);
    if (token) {
      // axios allows us to access the Authorization header and add to it
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },

  // second function
  (error) => {
    return Promise.reject(error);
  }
);


// now we start using api instead of default axios object
export default api;