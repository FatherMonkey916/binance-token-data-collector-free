import requests
import time
import pymongo
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

# MongoDB Connection
MONGODB_URI = "mongodb+srv://alertdb:NzRoML9MhR3sSKjM@cluster0.iittg.mongodb.net/alert3"
client = MongoClient(MONGODB_URI)
db = client["alert3"]

# Binance API Endpoint for Klines
BINANCE_URL = "https://api.binance.com/api/v3/klines"

# Parameters
TOKENS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]
INTERVAL = "1m"
LIMIT = 1000  # Max per request
TOTAL_RECORDS = 15000  # Maintain only the latest 15K records per token
SLEEP_TIME = 2  # Sleep to avoid rate limits

def create_time_series_collection():
    """Create time series collections for each token if they don't exist."""
    for token in TOKENS:
        collection_name = f"{token}_timeseries"
        if collection_name not in db.list_collection_names():
            db.create_collection(
                collection_name,
                timeseries={"timeField": "timestamp", "metaField": "token", "granularity": "minutes"}
            )
            print(f"Created time series collection: {collection_name}")

def fetch_price_data(symbol, start_time, end_time):
    """Fetch historical price data within given start and end times."""
    params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT, "startTime": start_time, "endTime": end_time}
    try:
        response = requests.get(BINANCE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return []

def save_to_mongodb(collection, data, token):
    """Save all items in response to MongoDB and ensure size limit."""
    if not data:
        return
    
    records = [
        {
            "token": token,
            "timestamp": datetime.fromtimestamp(entry[0] / 1000, timezone.utc),
            "open": float(entry[1]),
            "high": float(entry[2]),
            "low": float(entry[3]),
            "close": float(entry[4]),
            "volume": float(entry[5]),
            "close_time": datetime.fromtimestamp(entry[6] / 1000, timezone.utc),
            "quote_asset_volume": float(entry[7]),
            "num_trades": entry[8],
            "taker_buy_base_asset_volume": float(entry[9]),
            "taker_buy_quote_asset_volume": float(entry[10]),
            "ignore": entry[11]
        }
        for entry in data
    ]
    
    if records:
        collection.insert_many(records)
        print(f"Saved {len(records)} records to {collection.name}")
        delete_oldest_records(collection)

def delete_oldest_records(collection):
    """Ensure only the latest 15K records are kept."""
    record_count = collection.count_documents({})
    if record_count > TOTAL_RECORDS:
        excess = record_count - TOTAL_RECORDS
        oldest_records = collection.find({}, {"_id": 1}).sort("timestamp", 1).limit(excess)
        ids_to_delete = [record["_id"] for record in oldest_records]
        if ids_to_delete:
            collection.delete_many({"_id": {"$in": ids_to_delete}})
            print(f"Deleted {excess} old records from {collection.name}")

def fetch_initial_data():
    """Fetch initial 15K records per token."""
    for token in TOKENS:
        collection = db[f"{token}_timeseries"]
        if collection.count_documents({}) >= TOTAL_RECORDS:
            print(f"Database already has {TOTAL_RECORDS} records for {token}. Skipping initial fetch.")
            continue
        
        end_time = int(time.time() * 1000)
        fetched = 0
        retries = 0
        
        while fetched < TOTAL_RECORDS and retries < 5:
            start_time = end_time - (LIMIT * 60 * 1000)
            price_data = fetch_price_data(token, start_time, end_time)
            
            if not price_data:
                print(f"No data returned for {token}, retrying...")
                retries += 1
                time.sleep(5)
                continue
            
            save_to_mongodb(collection, price_data, token)
            fetched += len(price_data)
            # Move end_time to the start of the earliest fetched kline minus 1ms
            end_time = int(price_data[0][0]) - 1
            print(f"Total records saved for {token}: {fetched}/{TOTAL_RECORDS}")
            retries = 0  # Reset retries after successful fetch
            time.sleep(SLEEP_TIME)
        
        if fetched >= TOTAL_RECORDS:
            print(f"Successfully fetched {TOTAL_RECORDS} records for {token}.")
        else:
            print(f"Stopped fetching for {token} after {retries} retries. Total fetched: {fetched}")

def fill_gaps():
    """Fill missing minute gaps from the latest timestamp to now."""
    for token in TOKENS:
        collection = db[f"{token}_timeseries"]
        last_record = collection.find_one({}, sort=[("timestamp", -1)])
        if not last_record:
            continue
        
        last_timestamp = int(last_record["timestamp"].timestamp() * 1000)
        current_time = int(time.time() * 1000)
        gap_start = last_timestamp + 60000  # Start after last record
        
        while gap_start < current_time:
            gap_end = min(gap_start + (LIMIT * 60 * 1000), current_time)
            price_data = fetch_price_data(token, gap_start, gap_end)
            if not price_data:
                break  # No more data available
            
            save_to_mongodb(collection, price_data, token)
            if price_data:
                # Move gap_start to the end of the last fetched kline
                gap_start = int(price_data[-1][0]) + 60000
            else:
                break
            time.sleep(SLEEP_TIME)

def live_update():
    """Fetch new price data at exact minute marks and maintain record limits."""
    while True:
        current_time = datetime.now(timezone.utc)
        next_minute = (current_time + timedelta(minutes=1)).replace(second=0, microsecond=0)
        sleep_duration = (next_minute - current_time).total_seconds()
        if sleep_duration > 0:
            time.sleep(sleep_duration)
        
        # Wait an additional 5 seconds to ensure Binance data is available
        time.sleep(5)
        
        for token in TOKENS:
            collection = db[f"{token}_timeseries"]
            current_utc = datetime.now(timezone.utc)
            previous_minute = current_utc.replace(second=0, microsecond=0) - timedelta(minutes=1)
            start_time = int(previous_minute.timestamp() * 1000)
            end_time = start_time + 60 * 1000  # Next minute
            
            price_data = fetch_price_data(token, start_time, end_time)
            retries = 0
            while not price_data and retries < 3:
                print(f"No data for {token} at {previous_minute}, retrying...")
                time.sleep(2)
                price_data = fetch_price_data(token, start_time, end_time)
                retries += 1
            
            if price_data:
                save_to_mongodb(collection, price_data, token)
                print(f"Updated {token} at {previous_minute}")
            else:
                print(f"Failed to fetch data for {token} at {previous_minute}")
            
            delete_oldest_records(collection)

if __name__ == "__main__":
    try:
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        create_time_series_collection()
        fetch_initial_data()
        fill_gaps()
        live_update()
    except Exception as e:
        print(f"Error: {e}")