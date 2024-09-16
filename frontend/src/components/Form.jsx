import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";  // hook that allows us to access navigation from the code
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import LoadingIndicator from "./LoadingIndicator";


// the route that we want to go to and what method (login or register)
function Form({ route, method }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();



    const handleSubmit = async (e) => {
        setLoading(true);

        // prevent the form from automatically submitting and the page reloading
        // because we have custom form submission logic
        e.preventDefault();


        // attempt to send a request to the indicated route
        try {
            // if it's login, we submit credential to our backend, and we will get the two tokens back as the result
            const res = await api.post(route, { username, password })
            console.log(route)
            if (method === "login") {
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
                navigate("/")
            // if the method is register
            } else {
                navigate("/login")
            }
        } catch (error) {
            alert(error)
        } finally {
            setLoading(false)
        }
    };



    const name = method === "login" ? "Login" : "Register";




    return (
        <form onSubmit={handleSubmit} 
        className="flex flex-col items-center justify-center mx-auto my-12 p-5 rounded-lg max-w-md"
        style={{ boxShadow: "0 12px 20px rgba(255, 255, 255, 0.1), 0 6px 10px rgba(255, 255, 255, 0.06)"}}>
            <h1 className="text-24 lg:text-36 font-semibold text-white">
                {name}
            </h1>
            <input
                className="w-11/12 mt-5 p-3 mb-4 rounded-lg border-0 
                focus:outline-none focus:ring-2 focus:ring-blue-200
                bg-gray-700 text-white placeholder-gray-400 shadow-inner"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
            />

            <input
                className="w-11/12 mt-5 p-3 mb-4 rounded-lg border-0 
                focus:outline-none focus:ring-2 focus:ring-blue-200
                bg-gray-700 text-white placeholder-gray-400 shadow-inner"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            
            {loading && <LoadingIndicator />}

            <button className="form-btn" type="submit" disabled={loading}>
                {name}
            </button>
        </form>
    );
}


export default Form