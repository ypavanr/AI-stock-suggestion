from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

app = FastAPI(title="Predict Stock Category API", version="1.0")

merged_df = pd.read_csv("merged_stocks.csv")

features = ['Return', 'Volatility', 'beta', 'marketCap']
X_train = merged_df[features]
y_train = merged_df['Risk_Segment']

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train_scaled, y_train)

class CategoryRequest(BaseModel):
    ticker: str
    Return: float
    Volatility: float
    Beta: float
    Marketcap: int

@app.post("/get-stock-category")
def get_stock_category(request: CategoryRequest):
    new_data = [[
        request.Return,
        request.Volatility,
        request.Beta,
        request.Marketcap
    ]]
    
    new_data_scaled = scaler.transform(new_data)
    
    predicted_segment = knn.predict(new_data_scaled)[0]
    
    return {
        "ticker": request.ticker,
        "predicted_risk_segment": predicted_segment
    }
