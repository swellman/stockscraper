import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const StockPrice = () => {
  const [symbols, setSymbols] = useState(['AAPL']);
  const [prices, setPrices] = useState({});
  const [historicalData, setHistoricalData] = useState({});
  const [averages, setAverages] = useState({});
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPrices = async () => {
      setLoading(true);
      try {
        const responses = await Promise.all(symbols.map(symbol => axios.get(`http://127.0.0.1:5000/api/stocks/${symbol}`)));
        const newPrices = {};
        responses.forEach((response, index) => {
          newPrices[symbols[index]] = response.data.price;
        });
        setPrices(newPrices);
        setError(null);
      } catch (error) {
        setPrices({});
        setError('Error fetching stock prices');
        console.error('Error fetching stock prices:', error);
      } finally {
        setLoading(false);
      }
    };

    const fetchHistoricalData = async () => {
      setLoading(true);
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/historical/multiple', { symbols });
        setHistoricalData(response.data);
        setError(null);
      } catch (error) {
        setHistoricalData({});
        setError('Error fetching historical data');
        console.error('Error fetching historical data:', error);
      } finally {
        setLoading(false);
      }
    };

    const fetchAverages = async () => {
      setLoading(true);
      try {
        const responses = await Promise.all(symbols.map(symbol => axios.get(`http://127.0.0.1:5000/api/average/${symbol}?days=${days}`)));
        const newAverages = {};
        responses.forEach((response, index) => {
          newAverages[symbols[index]] = response.data.average_price;
        });
        setAverages(newAverages);
        setError(null);
      } catch (error) {
        setAverages({});
        setError('Error fetching average prices');
        console.error('Error fetching average prices:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPrices();
    fetchHistoricalData();
    fetchAverages();
  }, [symbols, days]);

  const handleInputChange = (e) => {
    const newSymbols = e.target.value.split(',').map(s => s.trim().toUpperCase());
    setSymbols(newSymbols);
  };

  const handleDaysChange = (e) => {
    setDays(e.target.value);
  };

  return (
    <div>
      <h1>Stock Scraper</h1>
      <input type="text" value={symbols.join(',')} onChange={handleInputChange} placeholder="Enter stock symbols, separated by commas" />
      <input type="number" value={days} onChange={handleDaysChange} placeholder="Enter number of days for average price" />
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p>{error}</p>
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
