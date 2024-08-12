import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";  // hook that allows us to access navigation from the code
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import "../styles/Form.css"
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
        <form onSubmit={handleSubmit} className="form-container">
            <h1>{name}</h1>
            <input
                className="form-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
            />

            <input
                className="form-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            
            {loading && <LoadingIndicator />}

            <button className="form-button" type="submit" disabled={loading}>
                {name}
            </button>
        </form>
    );
}


export default Form