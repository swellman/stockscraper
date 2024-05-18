import React, { useState, useEffect } from 'react'; // Import necessary hooks from React
import axios from 'axios'; // Import axios for making HTTP requests
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'; // Import Recharts components

const StockPrice = () => {
  const [symbols, setSymbols] = useState(['AAPL']); // State to hold stock symbols
  const [prices, setPrices] = useState({}); // State to hold current stock prices
  const [historicalData, setHistoricalData] = useState({}); // State to hold historical stock data
  const [averages, setAverages] = useState({}); // State to hold average stock prices
  const [days, setDays] = useState(30); // State to hold number of days for average calculation
  const [loading, setLoading] = useState(false); // State to manage loading status
  const [error, setError] = useState(null); // State to hold error messages

  // useEffect hook to fetch data when symbols or days change
  useEffect(() => {
    const fetchPrices = async () => {
      setLoading(true); // Set loading to true before fetching
      try {
        // Fetch current prices for each symbol
        const responses = await Promise.all(symbols.map(symbol => axios.get(`http://127.0.0.1:5000/api/stocks/${symbol}`)));
        const newPrices = {};
        responses.forEach((response, index) => {
          newPrices[symbols[index]] = response.data.price;
        });
        setPrices(newPrices); // Update prices state with fetched data
        setError(null); // Clear any previous errors
      } catch (error) {
        setPrices({}); // Clear prices if an error occurs
        setError('Error fetching stock prices'); // Set error message
        console.error('Error fetching stock prices:', error);
      } finally {
        setLoading(false); // Set loading to false after fetching
      }
    };

    const fetchHistoricalData = async () => {
      setLoading(true); // Set loading to true before fetching
      try {
        // Fetch historical data for all symbols
        const response = await axios.post('http://127.0.0.1:5000/api/historical/multiple', { symbols });
        setHistoricalData(response.data); // Update historical data state with fetched data
        setError(null); // Clear any previous errors
      } catch (error) {
        setHistoricalData({}); // Clear historical data if an error occurs
        setError('Error fetching historical data'); // Set error message
        console.error('Error fetching historical data:', error);
      } finally {
        setLoading(false); // Set loading to false after fetching
      }
    };

    const fetchAverages = async () => {
      setLoading(true); // Set loading to true before fetching
      try {
        // Fetch average prices for each symbol
        const responses = await Promise.all(symbols.map(symbol => axios.get(`http://127.0.0.1:5000/api/average/${symbol}?days=${days}`)));
        const newAverages = {};
        responses.forEach((response, index) => {
          newAverages[symbols[index]] = response.data.average_price;
        });
        setAverages(newAverages); // Update averages state with fetched data
        setError(null); // Clear any previous errors
      } catch (error) {
        setAverages({}); // Clear averages if an error occurs
        setError('Error fetching average prices'); // Set error message
        console.error('Error fetching average prices:', error);
      } finally {
        setLoading(false); // Set loading to false after fetching
      }
    };

    // Call the fetch functions when symbols or days change
    fetchPrices();
    fetchHistoricalData();
    fetchAverages();
  }, [symbols, days]);

  // Handler for changing the symbols input
  const handleInputChange = (e) => {
    const newSymbols = e.target.value.split(',').map(s => s.trim().toUpperCase());
    setSymbols(newSymbols); // Update symbols state with new values
  };

  // Handler for changing the number of days input
  const handleDaysChange = (e) => {
    setDays(e.target.value); // Update days state with new value
  };

  return (
    <div>
      <h1>Stock Scraper</h1>
      <input type="text" value={symbols.join(',')} onChange={handleInputChange} placeholder="Enter stock symbols, separated by commas" />
      <input type="number" value={days} onChange={handleDaysChange} placeholder="Enter number of days for average price" />
      {loading ? (
        <p>Loading...</p> // Display loading message if loading
      ) : error ? (
        <p>{error}</p> // Display error message if there's an error
      ) : (
        <>
          {symbols.map(symbol => (
            <div key={symbol}>
              <h2>{symbol}</h2>
              <p>Current Price: ${prices[symbol]}</p>
              <p>Average Price over {days} days: ${averages[symbol]}</p>
              {historicalData[symbol] && (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={historicalData[symbol]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="close" stroke="#8884d8" activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  );
};

export default StockPrice;
