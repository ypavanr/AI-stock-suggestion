from fastapi import FastAPI, HTTPException
import yfinance as yf
from pydantic import BaseModel
import pandas as pd
import requests
import numpy as np

app = FastAPI(title="Stock Details API", version="1.0")

PREDICT_API_URL = "http://predict-stock-category:8081/get-stock-category"

class StockRequest(BaseModel):
    ticker: str
    period: str = "1y"
    interval: str = "1d"

@app.post("/individual-stock/details")
def get_stock_details(request: StockRequest):
    try:
        def fetch_close_prices(tickers, start='2024-01-01', end='2025-01-01'):
            data = yf.download(tickers, start=start, end=end)['Close']
            data = data.stack().reset_index()
            data.columns = ['Date', 'Ticker', 'Close']
            return data

        close_data = fetch_close_prices(request.ticker)

        if close_data.empty:
            raise HTTPException(status_code=404, detail="No historical data found.")

        close_data['log_return'] = close_data.groupby('Ticker')['Close'].transform(
            lambda x: np.log(x / x.shift(1))
        )

        close_data['volatility_30d'] = close_data.groupby('Ticker')['log_return'].transform(
            lambda x: x.rolling(window=30).std()
        )
        close_data['return_30d'] = close_data.groupby('Ticker')['log_return'].transform(
            lambda x: x.rolling(30).mean()
        )

        latest_data = close_data.dropna().iloc[-1]
        latest_volatility = latest_data['volatility_30d']
        latest_return = latest_data['return_30d']

        ticker_obj = yf.Ticker(request.ticker)
        info = ticker_obj.info

        hist = ticker_obj.history(period=request.period, interval=request.interval)
        hist_graph = hist.reset_index()[["Date", "Close"]]
        hist_graph["Date"] = hist_graph["Date"].dt.strftime("%Y-%m-%d")

        category_payload = {
            "ticker": request.ticker.upper(),
            "Return": latest_return,  
            "Volatility": latest_volatility,
            "Beta": info.get("beta", 1.0) if info.get("beta") is not None else 1.0,
            "Marketcap": info.get("marketCap", 0)
        }

        try:
            category_response = requests.post(PREDICT_API_URL, json=category_payload)
            if category_response.status_code == 200:
                predicted_category = category_response.json().get("predicted_risk_segment", "Unknown")
            else:
                predicted_category = "Prediction service error"
        except Exception as e:
            predicted_category = f"Prediction request failed: {str(e)}"

        details = {
            "symbol": request.ticker.upper(),
            "company_name": info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "currency": info.get("currency"),
            "latest_30d_volatility": round(latest_volatility, 6),
            "latest_30d_return": round(latest_return, 6),
            "category(risk based)": predicted_category,
            "historical_data_for_graph": hist_graph.to_dict(orient="records")
        }

        return {"status": "success", "data": details}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
