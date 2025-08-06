from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import pandas as pd
import re

app = FastAPI()

stock_details = pd.read_csv("merged_stocks.csv")

AUTH_SVC_ADDRESS = os.environ.get("AUTH_SVC_ADDRESS", "auth:3000")

async def validate_token(request: Request):
    """Validate JWT using the auth service."""
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Missing credentials")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{AUTH_SVC_ADDRESS}/validate",
                headers={"Authorization": token}
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unreachable")

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


@app.get("/stock-preference/{preference}")
async def get_preferred_stocks(preference: str, user_data: dict = Depends(validate_token)):
    if not preference:
        raise HTTPException(status_code=400, detail="Missing preference")

    preferred_stock = stock_details[
        stock_details['risk_segment'].str.contains(preference, flags=re.IGNORECASE, regex=True, na=False)
    ]

    if preferred_stock.empty:
        raise HTTPException(status_code=404, detail="No stocks available in this category")

    result = preferred_stock[['ticker', 'marketCap', 'beta', 'currentPrice', 'sector']].to_dict(orient="records")
    return JSONResponse(content=result, status_code=200)


@app.get("/get-all-stocks")
async def get_all_stocks(user_data: dict = Depends(validate_token)):

    result = stock_details[['ticker', 'marketCap', 'beta', 'currentPrice', 'sector',"Risk_Segment"]].to_dict(orient="records")
    return JSONResponse(content=result, status_code=200)


    
 
