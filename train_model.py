import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

print("Starting AI Model Training Pipeline...")

# 1. Load Data
file_path = "output/fact_sensor.csv"
if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} not found. Please run the Batch Generator first.")
    exit(1)

print(f"Loading historical telemetry from {file_path}...")
# We use a random sample of 250,000 rows to speed up training,
# since the full dataset is ~288MB (millions of rows).
df = pd.read_csv(file_path).sample(n=250000, random_state=42)

# 2. Prepare Features & Labels
# We want to train the AI to recognize the patterns of "Warning" and "Error" states
print("Extracting features and labels...")
features = ['Temperature', 'Vibration', 'Power Consumption']
X = df[features]

# Label: 1 if the machine is in Error or Warning state, 0 if Running normally.
# This teaches the AI what a "High Risk" state looks like physically.
y = df['Running Status'].apply(lambda x: 1 if x in ['Error', 'Warning'] else 0)

# The simulation ran perfectly, so we have very few errors in the historical data.
# We will synthetically inject extreme high-temperature and high-vibration scenarios
# so the AI can learn what an impending failure looks like.
print("Synthesizing failure scenarios to balance the dataset...")
fail_temp = np.random.normal(110, 10, 5000)
fail_vib = np.random.normal(7.5, 1.0, 5000)
fail_pwr = np.random.normal(140, 15, 5000)

fail_df = pd.DataFrame({
    'Temperature': fail_temp,
    'Vibration': fail_vib,
    'Power Consumption': fail_pwr
})
fail_y = pd.Series([1] * 5000)

X = pd.concat([X, fail_df])
y = pd.concat([y, fail_y])

# 3. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train the AI (Random Forest)
print("Training Random Forest Classifier...")
model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# 5. Evaluate
print("Evaluating Model Performance...")
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print(classification_report(y_test, y_pred, target_names=['Normal (0)', 'Risk/Failure (1)']))

# 6. Save Model
model_path = "output/predictive_maintenance_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(model, f)
    
print(f"AI Model trained and saved successfully to: {model_path}")
print("The Live IoT Dashboard can now use this brain to predict Failure Risk in real-time!")
