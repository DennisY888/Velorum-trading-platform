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
  const [initialLoad, setInitialLoad] = useState(true);

  // Function to fetch the top 10 users
  const fetchTopUsers = useCallback(async () => {
    if (initialLoad) {
      setLoading(true);
    }
    try {
      const response = await api.get('/api/leaderboard/');
      setTopUsers(response.data);
      setInitialLoad(false);
    } catch (error) {
      console.error('Error fetching top users:', error);
    } finally {
      setLoading(false);
    }
  }, [initialLoad]);

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
    []
  );

  useEffect(() => {
    fetchFilteredUsers(searchQuery);
  }, [searchQuery, fetchFilteredUsers]);

  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value);
  }, []);

  const handleClick = (user) => {
    setSearchQuery('');
    setFilteredUsers([]);
  };

  const renderTableRows = useCallback(
    (users) => {
      return users.map((user) => (
        <tr key={user.user} className="hover:bg-slate-700">
          <td className="p-4">{user.user}</td>
          <td className="p-4">{user.total_value}</td>
          <td className="p-4">{user.ranking}</td>
        </tr>
      ));
    },
    [topUsers]
  );


  const renderDropdownItems = useCallback(
    (users) => {
      if (autoLoading) {
        return (
          <div className="p-4 hover:bg-slate-700 text-blue-100 cursor-pointer">
            <p>Loading...</p>
          </div>
        );
      } else if (users.length > 0) {
        return users.map((user) => (
          <div
            key={user.user}
            onClick={() => handleClick(user.user)}
            className="p-4 hover:bg-slate-700 text-blue-100 cursor-pointer"
          >
            <p>{user.user} - {user.total_value}</p>
            <p>Rank: {user.ranking}</p>
          </div>
        ));
      } else {
        return null; // Don't render anything if there's no data and not loading
      }
    },
    [autoLoading, filteredUsers]
  );


  
  if (loading && initialLoad) {
    return (
      <div className="loader-container">
        <div className="loader">
          <div></div><div></div><div></div><div></div>
        </div>
        <h1>Loading Leaderboard...</h1>
      </div>
    );
  }

  return (
    <div className="leaderboard-container">
      <h1 className="text-5xl font-bold text-blue-100 mb-6">Leaderboard</h1>
      
      {/* Search Input and Autocomplete */}
      <div className='w-full max-w-lg relative' style={{ margin: '0 auto 20px' }}>
        <input
          type="text"
          placeholder="Search for a user..."
          value={searchQuery}
          onChange={handleSearchChange}
          className="w-full p-4 text-xl rounded-full bg-slate-800 text-blue-100 placeholder-blue-400 focus:outline-none focus:ring-2 focus:ring-slate-600 caret-blue-200"
          style={{
            textShadow: '0 0 8px rgba(255, 255, 255, 0.7)',
            animation: 'glow 1s infinite alternate' // Blinking glow effect
          }}
        />
        {(searchQuery && (autoLoading || filteredUsers.length > 0)) && (
          <div className="absolute w-full mt-1 rounded-lg bg-gradient-to-r from-slate-800 to-slate-900 shadow-lg overflow-hidden z-10">
            {renderDropdownItems(filteredUsers)}
          </div>
        )}
      </div>

      {/* Leaderboard Table */}
      <table className="leaderboard-table">
        <thead>
          <tr className="bg-slate-800 text-blue-100">
            <th className="p-4">Username</th>
            <th className="p-4">Portfolio Value</th>
            <th className="p-4">Ranking</th>
          </tr>
        </thead>
        <tbody className="text-blue-100">
          {renderTableRows(topUsers)}
        </tbody>
      </table>
    </div>
  );
};

export default React.memo(Leaderboard);
