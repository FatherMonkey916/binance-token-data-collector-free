import requests
import time
import pymongo
from datetime import datetime

# MongoDB Connection
MONGODB_URI = "mongodb+srv://alertdb:NzRoML9MhR3sSKjM@cluster0.iittg.mongodb.net/alert3"
client = pymongo.MongoClient(MONGODB_URI)
db = client["alert3"]

# Binance API Endpoint for Klines
BINANCE_URL = "https://api.binance.com/api/v3/klines"

# Parameters
TOKENS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]
INTERVAL = "1m"
LIMIT = 1000  # Max allowed per request
TOTAL_RECORDS = 15000  # Maintain only the latest 15000 records per token
SLEEP_TIME = 2  # Sleep time to avoid API rate limits

def create_time_series_collection():
    """Create time series collections for each token if they don't exist."""
    for token in TOKENS:
        collection_name = f"{token}_timeseries"

        if collection_name not in db.list_collection_names():
            db.create_collection(
                collection_name,
                timeseries={
                    "timeField": "timestamp",
                    "metaField": "token",
                    "granularity": "minutes"
                }
            )
            print(f"Created time series collection: {collection_name}")

def fetch_price_data(symbol, start_time, end_time):
    """Fetch historical price data using startTime and endTime"""
    params = {
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": LIMIT,
        "startTime": start_time,
        "endTime": end_time
    }
    response = requests.get(BINANCE_URL, params=params)
    data = response.json()
    return data if isinstance(data, list) else []

def save_to_mongodb(collection, data, token):
    """Save price data to MongoDB time series collection and ensure size limit."""
    if not data:
        return
    
    records = [
        {
            "token": token,
            "price": float(entry[4]),  # Closing price
            "timestamp": datetime.fromtimestamp(entry[0] / 1000, datetime.timezone.utc)
        }
        for entry in data
    ]

    collection.insert_many(records)
    print(f"Saved {len(records)} records to {collection.name}")
    
    # Maintain only the latest 15000 records
    delete_oldest_records(collection)

def delete_oldest_records(collection):
    """Ensure that only the latest 15000 records are kept."""
    record_count = collection.count_documents({})
    if record_count > TOTAL_RECORDS:
        excess = record_count - TOTAL_RECORDS
        oldest_records = collection.find({}, {"_id": 1}).sort("timestamp", 1).limit(excess)
        ids_to_delete = [record["_id"] for record in oldest_records]
        collection.delete_many({"_id": {"$in": ids_to_delete}})
        print(f"Deleted {excess} old records from {collection.name}")

def fetch_initial_data():
    """Fetch initial 15000 records for each token"""
    for token in TOKENS:
        collection = db[f"{token}_timeseries"]
        end_time = int(time.time() * 1000)  # Current timestamp in milliseconds
        fetched = 0

        if collection.count_documents({}) >= TOTAL_RECORDS:
            print(f"Database already has {TOTAL_RECORDS} records for {token}. Skipping initial fetch.")
            continue

        while fetched < TOTAL_RECORDS:
            start_time = end_time - (LIMIT * 60 * 1000)  # Move back LIMIT minutes
            price_data = fetch_price_data(token, start_time, end_time)
            
            if not price_data:
                print(f"No data returned for {token}, retrying...")
                time.sleep(5)
                continue
            
            save_to_mongodb(collection, price_data, token)
            fetched += len(price_data)
            end_time = int(price_data[0][0]) - 1  # Update end_time for older data
            print(f"Total records saved for {token}: {fetched}/{TOTAL_RECORDS}")
            time.sleep(SLEEP_TIME)

def live_update():
    """Continuously update MongoDB for all tokens and maintain record limit."""
    while True:
        for token in TOKENS:
            collection = db[f"{token}_timeseries"]
            end_time = int(time.time() * 1000)
            start_time = end_time - (60 * 1000)  # Fetch only last 1-minute data
            price_data = fetch_price_data(token, start_time, end_time)
            
            if not price_data:
                print(f"No new data available for {token}, retrying...")
                time.sleep(1)  # Reduce sleep time to avoid missing data
                continue

            # Insert new record
            new_record = {
                "token": token,
                "price": float(price_data[0][4]),  # Closing price
                "timestamp": datetime.fromtimestamp(price_data[0][0] / 1000, datetime.timezone.utc)
            }
            collection.insert_one(new_record)
            print(f"Added new record for {token}: {new_record}")
            
            # Ensure only 15000 records are kept
            delete_oldest_records(collection)
            time.sleep(SLEEP_TIME)  # Reduce sleep to balance API requests
        
        time.sleep(60 - (SLEEP_TIME * len(TOKENS)))  # Ensure balanced API calls

if __name__ == "__main__":
    try:
        client.admin.command('ping')
        print("Pinged your deployment. Successfully connected to MongoDB!")

        # Create time series collections if not exist
        create_time_series_collection()

        # Fetch initial data if not already fetched
        fetch_initial_data()

        # Start live updating process
        live_update()
        
    except Exception as e:
        print(f"Error: {e}")
