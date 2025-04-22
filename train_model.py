import pandas as pd
import numpy as np
import pymysql
import joblib
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from config import DB_CONFIG

# Step 1: Fetch data from DB
try:
    conn = pymysql.connect(**DB_CONFIG)
    query = "SELECT * FROM current_sensor1"
    df = pd.read_sql(query, conn)
    conn.close()
    print("✅ Data fetched successfully")
except Exception as e:
    print(f"❌ DB Error: {e}")
    exit()

# Step 2: Clean & prepare
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df.fillna(0, inplace=True)

# Step 3: Use only relevant features
selected_features = [
    "value", "rolling_mean", "slope", 
    "upper_limit", "lower_limit", "degradation_score"
]

# Check if all columns are present
missing = [col for col in selected_features if col not in df.columns]
if missing:
    print(f"❌ Missing columns in DB: {missing}")
    exit()

X_full = df[selected_features]

# Step 4: Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_full)

# Step 5: Unsupervised Anomaly Detection (Isolation Forest)
iso_forest = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
anomaly_labels = iso_forest.fit_predict(X_scaled)
df["anomaly_label"] = (anomaly_labels == -1).astype(int)

print(f"🚨 Anomalies detected: {df['anomaly_label'].sum()} / {len(df)}")

# Step 6: Supervised XGBoost Training
X = X_full
y = df["anomaly_label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)

xgb_model = xgb.XGBClassifier(
    n_estimators=300,
    learning_rate=0.01,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=(y == 0).sum() / (y == 1).sum(),
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42
)

xgb_model.fit(X_train, y_train, 
              eval_set=[(X_test, y_test)],
              early_stopping_rounds=10,
              verbose=False)

# Step 7: Evaluation
y_pred = xgb_model.predict(X_test)

acc = accuracy_score(y_test, y_pred)
print(f"✅ XGBoost Accuracy: {acc:.4f}")

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
            xticklabels=["Normal", "Anomaly"], 
            yticklabels=["Normal", "Anomaly"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.tight_layout()
plt.savefig("confusion_matrix.png")
print("📈 Confusion matrix saved: confusion_matrix.png")

# Step 8: Save Models
joblib.dump(iso_forest, "isolation_forest_model.pkl")
joblib.dump(xgb_model, "xgboost_classifier.pkl")
joblib.dump(scaler, "combo_scaler.pkl")

print("✅ Final Isolation Forest + XGBoost model saved successfully (degradation features only)!")
