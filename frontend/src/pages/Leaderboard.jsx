import React, { useState, useEffect, useCallback } from 'react';
import api from "../api";
import debounce from 'lodash.debounce'; // delays triggering of API call for autocomplete search
import "../styles/Leaderboard.css";

const Leaderboard = () => {
  const [topUsers, setTopUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoLoading, setAutoLoading] = useState(false);



  // Function to fetch the top 10 users
  const fetchTopUsers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/leaderboard/');
      setTopUsers(response.data);
    } catch (error) {
      console.error('Error fetching top users:', error);
    } finally {
      setLoading(false);
    }
  }, []);



  // Fetch top 10 users on component mount and every minute for real-time updates
  useEffect(() => {
    fetchTopUsers(); // Initial fetch on mount

    const intervalId = setInterval(() => {
      fetchTopUsers();
    }, 60000); // Fetch every 60 seconds

    return () => clearInterval(intervalId); // Cleanup interval on component unmount
  }, [fetchTopUsers]);



  // Debounced search input change
  const fetchFilteredUsers = useCallback(
    debounce(async (query) => {
      if (query !== '') {
        setAutoLoading(true);
        try {
          const response = await api.get(`/api/leaderboard/?q=${query}`);
          setFilteredUsers(response.data);
        } catch (error) {
          console.error('Error fetching filtered users:', error);
        } finally {
          setAutoLoading(false); // Reset loading state after the API call
        }
      } else {
        setFilteredUsers([]);
        setAutoLoading(false);
      }
    }, 300),
    []);



  useEffect(() => {
    fetchFilteredUsers(searchQuery);
  }, [searchQuery, fetchFilteredUsers]);



  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value);
  }, []);



  const renderTableRows = useCallback(
    (users) => {
      return users.map((user) => (
        <tr key={user.user}>
          <td>{user.user}</td>
          <td>{user.total_value}</td>
          <td>{user.ranking}</td>
        </tr>
      ));
    },
    [topUsers]
  );



  const renderDropdownItems = useCallback(
    (users) => {
      if (autoLoading) {
        return (
          <div className="autocomplete-item">
            <p>Loading...</p>
          </div>
        );
      } else if (users.length > 0) {
        return users.map((user) => (
          <div key={user.user} className="autocomplete-item">
            <p>{user.user}</p>
            <p>{user.total_value}</p>
            <p>Rank: {user.ranking}</p>
          </div>
        ));
      } else {
        return null; // Don't render anything if there's no data and not loading
      }
    },
    [autoLoading, filteredUsers]
  );



  if (loading) {
    return <h1>Loading...</h1>;
  }



  return (
    <div className="leaderboard-container">
      <h1>Leaderboard</h1>
      <input
        type="text"
        placeholder="Search for a user..."
        value={searchQuery}
        onChange={handleSearchChange}
        className="search-bar"
      />
      {(searchQuery && (autoLoading || filteredUsers.length > 0)) && (
        <div className="autocomplete-dropdown">
          {renderDropdownItems(filteredUsers)}
        </div>
      )}
      <table className="leaderboard-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Portfolio Value</th>
            <th>Ranking</th>
          </tr>
        </thead>
        <tbody>
          {renderTableRows(topUsers)}
        </tbody>
      </table>
    </div>
  );
};

export default React.memo(Leaderboard);
