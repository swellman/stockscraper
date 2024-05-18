from flask import Flask, jsonify, request  # Import Flask and necessary modules
from flask_cors import CORS  # Import CORS for handling cross-origin requests
from flask_caching import Cache  # Import Cache for caching responses
from sqlalchemy import create_engine  # Import create_engine from SQLAlchemy for database connection
from sqlalchemy.orm import sessionmaker  # Import sessionmaker from SQLAlchemy for session management
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML
import requests  # Import requests for making HTTP requests
import datetime  # Import datetime for date and time manipulation
import time  # Import time for sleep functionality
from models import Base, Stock, HistoricalData  # Import ORM models

# Initialize Flask app
app = Flask(__name__)
# Enable CORS to allow cross-origin requests
CORS(app)
# Setup cache with SimpleCache type
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# API key for RapidAPI
RAPIDAPI_KEY = '619ce8009cmsh1c80aa29171feb8p1cd979jsn65c59742b178'  # Replace with your RapidAPI key
# Database URL for SQLite
DATABASE_URL = 'sqlite:///stocks.db'

# Setup SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Endpoint to get the current stock price
@app.route('/api/stocks/<symbol>', methods=['GET'])
@cache.cached(timeout=60*10, query_string=True)
def get_stock(symbol):
    # URL for fetching stock price from Google Finance
    url = f'https://www.google.com/finance/quote/{symbol}:NASDAQ'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        # Extract stock price from the HTML
        price_span = soup.find('div', {'class': 'YMlKec fxKbKc'})
        if price_span:
            price = price_span.text
        else:
            return jsonify({'error': 'Could not find the stock price on the page'}), 404
    except AttributeError:
        return jsonify({'error': 'Failed to parse the stock price from the page'}), 500
    
    return jsonify({'symbol': symbol, 'price': price})

# Endpoint to get historical data for a stock
@app.route('/api/historical/<symbol>', methods=['GET'])
@cache.cached(timeout=60*60, query_string=True)
def get_historical_data(symbol):
    try:
        # Check if the stock exists in the database, if not create it
        stock = session.query(Stock).filter_by(symbol=symbol).first()
        if not stock:
            stock = Stock(symbol=symbol)
            session.add(stock)
            session.commit()
        
        # URL for fetching historical data from Yahoo Finance
        url = f'https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-historical-data?symbol={symbol}&region=US'
        headers = {
            'x-rapidapi-host': 'apidojo-yahoo-finance-v1.p.rapidapi.com',
            'x-rapidapi-key': RAPIDAPI_KEY
        }

        # Attempt to fetch data, retry with exponential backoff if rate-limited
        for i in range(5):
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                break
            elif response.status_code == 429:
                time.sleep(2 ** i)
            else:
                return jsonify({'error': 'Failed to fetch historical data', 'status_code': response.status_code, 'text': response.text}), response.status_code

        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch historical data', 'status_code': response.status_code, 'text': response.text}), response.status_code

        data = response.json()
        if 'prices' not in data:
            return jsonify({'error': 'Failed to fetch historical data', 'data': data}), 500

        # Parse historical data and store it in the database
        historical_data = data['prices']
        parsed_data = [
            {'date': datetime.datetime.fromtimestamp(entry['date']).strftime('%Y-%m-%d'), 'close': entry['close']}
            for entry in historical_data if 'close' in entry
        ]

        for entry in parsed_data:
            date = datetime.datetime.strptime(entry['date'], '%Y-%m-%d').date()
            close = entry['close']
            record = session.query(HistoricalData).filter_by(stock_id=stock.id, date=date).first()
            if not record:
                new_record = HistoricalData(stock_id=stock.id, date=date, close=close)
                session.add(new_record)
        session.commit()

        return jsonify({'symbol': symbol, 'data': parsed_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to get historical data for multiple stocks
@app.route('/api/historical/multiple', methods=['POST'])
def get_historical_data_multiple():
    symbols = request.json.get('symbols', [])
    if not symbols:
        return jsonify({'error': 'No symbols provided'}), 400

    results = {}
    for symbol in symbols:
        try:
            # Check if the stock exists in the database, if not create it
            stock = session.query(Stock).filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(symbol=symbol)
                session.add(stock)
                session.commit()

            # URL for fetching historical data from Yahoo Finance
            url = f'https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-historical-data?symbol={symbol}&region=US'
            headers = {
                'x-rapidapi-host': 'apidojo-yahoo-finance-v1.p.rapidapi.com',
                'x-rapidapi-key': RAPIDAPI_KEY
            }

            # Attempt to fetch data, retry with exponential backoff if rate-limited
            for i in range(5):
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    break
                elif response.status_code == 429:
                    time.sleep(2 ** i)
                else:
                    results[symbol] = {'error': 'Failed to fetch historical data', 'status_code': response.status_code, 'text': response.text}
                    continue

            if response.status_code != 200:
                results[symbol] = {'error': 'Failed to fetch historical data', 'status_code': response.status_code, 'text': response.text}
                continue

            data = response.json()
            if 'prices' not in data:
                results[symbol] = {'error': 'Failed to fetch historical data', 'data': data}
                continue

            # Parse historical data and store it in the database
            historical_data = data['prices']
            parsed_data = [
                {'date': datetime.datetime.fromtimestamp(entry['date']).strftime('%Y-%m-%d'), 'close': entry['close']}
                for entry in historical_data if 'close' in entry
            ]

            for entry in parsed_data:
                date = datetime.datetime.strptime(entry['date'], '%Y-%m-%d').date()
                close = entry['close']
                record = session.query(HistoricalData).filter_by(stock_id=stock.id, date=date).first()
                if not record:
                    new_record = HistoricalData(stock_id=stock.id, date=date, close=close)
                    session.add(new_record)
            session.commit()

            results[symbol] = parsed_data
        except Exception as e:
            results[symbol] = {'error': str(e)}

    return jsonify(results)

# Endpoint to get the average stock price over a specified number of days
@app.route('/api/average/<symbol>', methods=['GET'])
def get_average_price(symbol):
    try:
        # Get the number of days for the average calculation from the query parameters
        days = request.args.get('days', default=30, type=int)
        stock = session.query(Stock).filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'error': 'Stock not found'}), 404

        cutoff_date = datetime.datetime.now().date() - datetime.timedelta(days=days)
        historical_data = session.query(HistoricalData).filter(HistoricalData.stock_id == stock.id, HistoricalData.date >= cutoff_date).all()

        if not historical_data:
            return jsonify({'error': 'No historical data found'}), 404

        # Calculate the average closing price
        average_price = sum([data.close for data in historical_data]) / len(historical_data)

        return jsonify({'symbol': symbol, 'average_price': average_price, 'days': days})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
