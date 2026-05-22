from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import pandas as pd
from google import genai
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# --- 1. CONFIGURE GEMINI SECURELY ---
# Load the hidden variables from the .env file
load_dotenv()

# --- 1. CONFIGURE GEMINI ---
# Fetch the key securely
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ No API key found! Please check your .env file.")

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="AI Fraud Detection API with PostgreSQL")

# --- 2. CONNECT TO POSTGRESQL & CREATE TABLE ---
try:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist yet
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_alerts (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(50),
            user_id VARCHAR(50),
            amount FLOAT,
            time_since_last_txn FLOAT,
            fraud_probability FLOAT,
            explanation TEXT,
            alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("🗄️ PostgreSQL Database Connected & Table Ready!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    conn = None

# --- 3. LOAD XGBOOST MODEL ---
try:
    with open('fraud_xgboost_model.pkl', 'rb') as f:
        xgboost_model = pickle.load(f)
    print("🧠 XGBoost Model Loaded Successfully!")
except FileNotFoundError:
    print("❌ Model file not found.")
    xgboost_model = None

class TransactionData(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    time_since_last_txn: float

# --- 4. PREDICTION ENDPOINT ---
@app.post("/predict")
def predict_fraud(data: TransactionData):
    if xgboost_model is None:
        return {"error": "Model not loaded"}

    input_data = pd.DataFrame([{
        'TransactionAmount': data.amount,
        'Time_Since_Last': data.time_since_last_txn
    }])

    prediction = int(xgboost_model.predict(input_data)[0])
    probability = float(xgboost_model.predict_proba(input_data)[0][1])

    is_fraud = True if prediction == 1 else False
    
    # -- TEMPORARY OVERRIDE FOR TESTING --
    if data.amount > 500:
        is_fraud = True
        probability = 0.99

    explanation = "Normal transaction behavior detected."

    # --- 5. TRIGGER GEMINI & SAVE TO DATABASE ---
    if is_fraud:
        print(f"\n🚨 FRAUD ALERT! TXN: {data.transaction_id} | Amount: ${data.amount}")
        
        prompt = f"""
        You are a fraud analyst. A transaction was flagged.
        Amount: ${data.amount}
        Seconds since last transaction: {data.time_since_last_txn}
        
        Write one short sentence explaining why this might be suspicious.
        """
        
        try:
            print("   ⏳ Asking Gemini for an explanation...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            explanation = response.text.strip()
            print(f"   🤖 Gemini Explanation: {explanation}")
            
            # --- SAVE TO POSTGRESQL ---
            if conn:
                cursor.execute("""
                    INSERT INTO fraud_alerts 
                    (transaction_id, user_id, amount, time_since_last_txn, fraud_probability, explanation)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (data.transaction_id, data.user_id, data.amount, data.time_since_last_txn, probability, explanation))
                print("   💾 Successfully saved to PostgreSQL database!\n")
                
        except Exception as e:
            explanation = "AI explanation unavailable."
            print(f"   ❌ Error (Gemini or Database): {e}")
            
    else:
        print(f"✅ Normal TXN: {data.transaction_id} | Amount: ${data.amount}")

    return {
        "transaction_id": data.transaction_id,
        "prediction": "Fraud" if is_fraud else "Normal",
        "fraud_probability": probability,
        "explanation": explanation
    }