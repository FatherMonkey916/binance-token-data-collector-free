import requests
import time
import pymongo
from datetime import datetime

# MongoDB Connection
MONGODB_URI = "mongodb+srv://alertdb:NzRoML9MhR3sSKjM@cluster0.iittg.mongodb.net/alert3"
client = pymongo.MongoClient(MONGODB_URI)
db = client["alert3"]
collection = db["price_data_15k"]

# Binance API Endpoint for Klines
BINANCE_URL = "https://api.binance.com/api/v3/klines"

# Parameters
SYMBOL = "SOLUSDT"
INTERVAL = "1m"
LIMIT = 1000  # Max allowed per request
TOTAL_RECORDS = 15000  # Total required records
SLEEP_TIME = 1  # Sleep time to avoid API rate limits

def fetch_price_data(start_time, end_time):
    """Fetch historical SOL price data using startTime and endTime"""
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": LIMIT,
        "startTime": start_time,
        "endTime": end_time
    }
    response = requests.get(BINANCE_URL, params=params)
    data = response.json()
    return data if isinstance(data, list) else []

def save_to_mongodb(data):
    """Save price data to MongoDB"""
    if not data:
        return
    
    records = [
        {
            "token": "SOL",
            "price": float(entry[4]),  # Closing price
            "timestamp": datetime.utcfromtimestamp(entry[0] / 1000)
        }
        for entry in data
    ]
    
    collection.insert_many(records)
    print(f"Saved {len(records)} records to MongoDB")

def fetch_initial_data():
    """Fetch initial 15,000 records using startTime and endTime"""
    end_time = int(time.time() * 1000)  # Current timestamp in milliseconds
    fetched = 0

    if collection.count_documents({}) >= TOTAL_RECORDS:
        print("Database already has 15,000 records. Skipping initial fetch.")
        return

    while fetched < TOTAL_RECORDS:
        start_time = end_time - (LIMIT * 60 * 1000)  # Move back LIMIT minutes
        price_data = fetch_price_data(start_time, end_time)
        
        if not price_data:
            print("No data returned, retrying...")
            time.sleep(5)
            continue
        
        save_to_mongodb(price_data)
        fetched += len(price_data)
        end_time = int(price_data[0][0]) - 1  # Update end_time for older data
        print(f"Total records saved: {fetched}/{TOTAL_RECORDS}")
        time.sleep(SLEEP_TIME)

def live_update():
    """Continuously update MongoDB by adding new record and removing oldest"""
    while True:
        end_time = int(time.time() * 1000)
        start_time = end_time - (60 * 1000)  # Fetch only last 1-minute data
        price_data = fetch_price_data(start_time, end_time)
        
        if not price_data:
            print("No new data available, retrying...")
            time.sleep(60)
            continue

        # Insert new record
        new_record = {
            "token": "SOL",
            "price": float(price_data[0][4]),  # Closing price
            "timestamp": datetime.utcfromtimestamp(price_data[0][0] / 1000)
        }
        collection.insert_one(new_record)
        print(f"Added new record: {new_record}")

        # Remove oldest record if size exceeds 15,000
        if collection.count_documents({}) > TOTAL_RECORDS:
            oldest_record = collection.find_one(sort=[("timestamp", pymongo.ASCENDING)])
            collection.delete_one({"_id": oldest_record["_id"]})
            print(f"Removed oldest record: {oldest_record}")

        time.sleep(60)  # Run every minute

if __name__ == "__main__":
    try:
        client.admin.command('ping')
        print("Pinged your deployment. Successfully connected to MongoDB!")

        # Fetch initial data if not already fetched
        fetch_initial_data()

        # Start live updating process
        live_update()
        
    except Exception as e:
        print(f"Error: {e}")
