import pandas as pd
import xgboost as xgb
import pickle

print("🎓 Training XGBoost Fraud Detection Model...")

# 1. Load the historical data
# Make sure this points to your actual CSV file!
df = pd.read_csv('data/raw_transactions.csv')

# 2. Prepare the Data (Feature Engineering)
# For this prototype, we will use Amount and a dummy 'Time_Since_Last' feature
# In reality, you'd calculate time gaps from historical data
df['Time_Since_Last'] = df['TransactionAmount'].apply(lambda x: 10 if x > 800 else 86400) 

# Create a mock 'Is_Fraud' column for training
# Let's say high amounts with fast times are fraudulent
df['Is_Fraud'] = ((df['TransactionAmount'] > 500) & (df['Time_Since_Last'] < 60)).astype(int)

# Features (X) and Target (y)
X = df[['TransactionAmount', 'Time_Since_Last']]
y = df['Is_Fraud']

# 3. Train the Model
model = xgb.XGBClassifier(eval_metric='logloss')
model.fit(X, y)

# 4. Save the Model to your hard drive
with open('fraud_xgboost_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Model trained and saved as 'fraud_xgboost_model.pkl'")