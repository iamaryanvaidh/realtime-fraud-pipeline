import pandas as pd
from confluent_kafka import Producer
import json
import time

# 1. Connect to Kafka using the official Confluent Library
producer = Producer({'bootstrap.servers': 'localhost:9092'})

TOPIC_NAME = 'bank-transactions'

# 2. Load your original dataset
print("Loading transaction data...")
try:
    # IMPORTANT: Ensure this filename exactly matches what is in your 'data' folder
    df = pd.read_csv('data/raw_transactions.csv') 
except FileNotFoundError:
    print("Error: Could not find the CSV file in the 'data' folder.")
    exit()

print(f"✅ Connected to Kafka. Starting live stream of {len(df)} transactions...\n")

# 3. Stream the data (1 transaction per second)
for index, row in df.iterrows():
    transaction = row.to_dict()
    
    # Convert the Python dictionary to JSON bytes
    transaction_bytes = json.dumps(transaction).encode('utf-8')
    
    # Send to Kafka
    producer.produce(TOPIC_NAME, value=transaction_bytes)
    producer.poll(0) # This tells the library to clear its internal memory buffer
    
    # Print to terminal
    txn_id = transaction.get('TransactionID', f'TXN_{index}')
    amount = transaction.get('TransactionAmount', 0)
    print(f"🚀 Sent -> ID: {txn_id} | Amount: ${amount}")
    
    # Wait 1 second before the next swipe
    time.sleep(1)

# Ensure everything finishes sending before closing
producer.flush()