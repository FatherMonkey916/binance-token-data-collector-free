## AI Trading Bot Data Collector: Real-Time Cryptocurrency Prices

This project is a data collector for AI modeling in AI trading bot development. It fetches and stores cryptocurrency price data from Binance into a MongoDB time series database. Here's a detailed description of the project:

## Project Overview

The script collects real-time and historical price data for multiple cryptocurrency trading pairs (BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, ADAUSDT) from the Binance API. It stores this data in MongoDB time series collections, maintaining a rolling window of the latest 15,000 records for each trading pair.

## Key Features

1. **Time Series Data Collection**: Utilizes Binance's API to fetch minute-by-minute (1m interval) candlestick data for specified cryptocurrency pairs[1].

2. **MongoDB Time Series Collections**: Creates and manages time series collections in MongoDB, optimized for time-based queries and analysis[2][4].

3. **Initial Data Backfill**: Fetches historical data to populate the database with the last 15,000 records for each trading pair if not already present.

4. **Live Updates**: Continuously fetches and stores the latest price data, ensuring the database always contains up-to-date information.

5. **Data Management**: Maintains a fixed number of records (15,000) per trading pair by automatically removing the oldest data when new data is added.

6. **Rate Limiting**: Implements sleep intervals to respect Binance API rate limits and avoid potential bans or timeouts.

## Technical Details

- **Language**: Python
- **APIs**: Binance REST API
- **Database**: MongoDB (with time series collections)
- **Key Libraries**: 
  - `requests` for API calls
  - `pymongo` for MongoDB interactions
  - `datetime` and `time` for timestamp management

## Code Structure

1. **MongoDB Connection**: Establishes a connection to a MongoDB Atlas cluster.
2. **Time Series Collection Creation**: Sets up time series collections for each trading pair if they don't exist.
3. **Data Fetching**: Functions to retrieve historical and live price data from Binance.
4. **Data Storage**: Methods to save fetched data to MongoDB and manage the collection size.
5. **Initial Data Population**: Fetches and stores historical data if the collections are empty or underpopulated.
6. **Live Update Loop**: Continuously fetches and stores the latest price data for all trading pairs.

## Usage in AI Trading Bot Development

This data collector serves as a crucial component in AI trading bot development:

1. **Historical Data Analysis**: The collected data can be used to train and backtest AI models for pattern recognition and trend analysis.
2. **Real-time Decision Making**: The live update feature ensures that AI models have access to the most recent market data for making trading decisions.
3. **Feature Engineering**: The minute-by-minute data allows for the creation of various technical indicators and custom features for AI models.
4. **Model Validation**: The historical data can be used to validate and refine AI trading strategies over different market conditions.