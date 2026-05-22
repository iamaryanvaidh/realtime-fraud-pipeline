# 🏦 Real-Time Bank Fraud Streaming Pipeline & GenAI Investigator

## 📌 Enterprise Overview
An end-to-end, event-driven machine learning microservice designed to process financial transactions in real-time. This pipeline decouples data ingestion from heavy ML compute, predicting fraud probabilities on the fly while handling severe class imbalances. 

To bridge the gap between raw machine learning outputs and human fraud investigators, the system integrates **Generative AI** to automatically write natural-language context reports for any flagged transactions.

## 🏗️ System Architecture & Data Flow
Data Generator ➔ Kafka Topic ➔ Consumer + Redis Cache ➔ FastAPI + XGBoost ➔ Gemini LLM ➔ PostgreSQL ➔ Streamlit UI

1. **Stream Ingestion (Apache Kafka):** Simulated live credit card transactions are published continuously to a Kafka topic, decoupling the data source from the processing engine.
2. **Stateful Feature Engineering (Redis):** As transactions arrive, an in-memory Redis cache calculates stateful velocity features (e.g., *time since the last transaction for this specific user*) in milliseconds.
3. **Inference Engine (FastAPI + XGBoost):** A scalable FastAPI microservice consumes the Kafka stream and passes the enriched data to an optimized XGBoost classifier trained specifically on highly imbalanced anomaly data.
4. **Explainable AI Layer (Google Gemini):** If a transaction is flagged as fraudulent, the system triggers the Gemini API to dynamically generate a human-readable explanation of *why* the transaction looks suspicious based on the feature weights.
5. **Observability & Storage (PostgreSQL + Streamlit):** All transactions, predictions, and GenAI explanations are securely persisted in a PostgreSQL database and visualized in a live, auto-refreshing Streamlit dashboard.

## 💻 Tech Stack
* **Message Broker:** Apache Kafka
* **In-Memory Cache:** Redis
* **Backend API:** FastAPI (Python)
* **Machine Learning:** XGBoost, Pandas, Scikit-Learn
* **Generative AI:** Google Gemini API
* **Database:** PostgreSQL
* **Frontend/Dashboard:** Streamlit
* **Containerization:** Docker & Docker Compose

## 🚀 Key Engineering Features
* **Sub-Second Latency:** Utilizes Redis as a high-speed feature store to prevent database bottlenecks during live model inference.
* **Imbalanced Classification:** XGBoost model is strictly tuned using dynamic class-weighting (`scale_pos_weight`) to optimize for Recall and F1-Score rather than baseline accuracy.
* **Automated Investigation Reports:** Replaces manual data auditing by using Gemini to translate tabular feature anomalies into plain English for security teams.
* **Full Containerization:** The entire distributed system (Zookeeper, Kafka, Redis, Postgres, FastAPI, Streamlit) is orchestrated via Docker Compose for one-click deployment.

## ⚙️ Local Installation & Setup

**1. Clone the repository & Install required libraries**
```bash
git clone https://github.com/iamaryanvaidh/real-time-fraud-pipeline
cd real-time-fraud-pipeline
pip install -r requirements.txt
```

**2. Create a `.env` file in root directory & Add your credentials**
```bash
GEMINI_API_KEY="your_google_gemini_api_key"
POSTGRES_USER="admin"
POSTGRES_PASSWORD="adminpassword"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_DB="fraud_db"
```

**3. Start the Infrastructure (Docker)**
```bash
docker-compose up -d
```

**4. Start the Infrastructure (Docker)**
You will need to open **4 separate terminal** windows to run the distributed system:

* **Terminal 1: Start the AI Brain (FastAPI)**
```bash
uvicorn model_api:app --reload
```

* **Terminal 2: Start the Kafka Consumer**
```bash
python consumer.py
```

* **Terminal 3: Launch the Live Dashboard (Streamlit)**
```bash
streamlit run dashboard.py
```

* **Terminal 4: Start the Live Transaction Stream (Producer)**
```bash
python producer.py
```

Watch the Streamlit dashboard automatically populate with live fraud alerts and custom AI-generated explanations!
