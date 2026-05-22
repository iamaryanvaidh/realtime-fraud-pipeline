import json
import time
from confluent_kafka import Consumer, KafkaError
import redis
import requests
import pandas as pd # Using pandas to easily calculate time differences

# 1. Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("🧠 Connected to Redis successfully!")
except redis.ConnectionError:
    print("❌ Could not connect to Redis. Is Docker running?")
    exit()

# 2. Configure Kafka Consumer
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'fraud_detection_group',
    'auto.offset.reset': 'latest'
}
consumer = Consumer(conf)
consumer.subscribe(['bank-transactions'])

print("🎧 Listening for live transactions from Kafka...\n")

# URL of our new FastAPI server
API_URL = "http://localhost:8000/predict"

try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None: continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF: continue
            else:
                print(f"⏳ Waiting for Producer... ({msg.error().code()})")
                time.sleep(2)
                continue

        # Extract transaction data
        transaction = json.loads(msg.value().decode('utf-8'))
        txn_id = transaction.get('TransactionID', 'Unknown')
        customer_id = transaction.get('CustomerID', 'Unknown_User')
        txn_time_str = transaction.get('TransactionDate', transaction.get('Time', 'N/A'))
        amount = transaction.get('TransactionAmount', transaction.get('Amount', 0))

        # -- REDIS FEATURE ENGINEERING --
        last_time_str = r.get(f"user:{customer_id}:last_txn")
        r.set(f"user:{customer_id}:last_txn", txn_time_str)

        time_diff_seconds = -1.0 # Default if no history
        
        # Calculate exactly how many seconds have passed since their last swipe
        if last_time_str and txn_time_str != 'N/A':
            try:
                current_time = pd.to_datetime(txn_time_str)
                previous_time = pd.to_datetime(last_time_str)
                time_diff_seconds = abs((current_time - previous_time).total_seconds())
            except Exception as e:
                pass # If date format is weird, ignore for now

        # --- AI & ML PREDICTION API CALL ---
        # Package the raw data + the Redis context
        payload = {
            "transaction_id": str(txn_id),
            "user_id": str(customer_id),
            "amount": float(amount),
            "time_since_last_txn": float(time_diff_seconds)
        }

        # Send to FastAPI
        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()
            
            # Print the final verdict
            if result['prediction'] == 'Fraud':
                # Grab the Gemini explanation safely
                gemini_text = result.get('explanation', 'No explanation provided.')
                print(f"🚨 FRAUD BLOCKED -> TXN: {txn_id} | Amt: ${amount}\n   🤖 AI Reason: {gemini_text}\n")
            else:
                print(f"✅ APPROVED -> TXN: {txn_id} | Amt: ${amount}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot reach FastAPI server. Is model_api.py running?")
            time.sleep(2)

except KeyboardInterrupt:
    print("\n🛑 Stopping consumer...")
finally:
    consumer.close()