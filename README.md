# **AI Trading Bot Data Collector | Binance Crypto Price**  

This project is a **cryptocurrency price data collector** that fetches **historical and live market data** from the Binance API and stores it in a **MongoDB time-series database**. The system ensures a continuous, up-to-date record of key trading pairs while maintaining a rolling history of **15,000 records per token**.

## **Features**  
- **Fetches live price data** for BTC, ETH, SOL, XRP, and ADA at **1-minute intervals**.  
- **Stores data in MongoDB** using **time-series collections** for efficient querying.  
- **Maintains a rolling window** of the most recent **15,000 records per token**.  
- **Fills historical data gaps** to ensure complete time-series consistency.  
- **Auto-retries on API failures** to improve data reliability.  

## **How It Works**  
1. **Initial Data Fetch**: Collects up to 15,000 historical records per token.  
2. **Gap Filling**: Detects and fills missing data points to maintain a complete time series.  
3. **Live Updates**: Fetches and stores new price data at each minute mark.  
4. **Data Pruning**: Ensures only the latest 15,000 records per token are kept.  

## **Setup & Usage**  
- Clone the repository  
- Install dependencies (`requests`, `pymongo`)  
- Set up a **MongoDB Atlas database**  
- Run the script to start collecting data  

This project is useful for **crypto traders, analysts, and developers** looking to maintain a structured and efficient historical price database for further analysis or algorithmic trading. 🚀  
