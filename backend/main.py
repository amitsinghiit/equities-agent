from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import pandas as pd
import json
from cachetools import TTLCache
from datetime import datetime

# Import our engines
from data_engine import get_stock_data
from technical_engine import calculate_technicals
from fundamental_engine import extract_fundamentals, analyze_fundamentals
from scoring_engine import calculate_score
from screener_scraper import scrape_screener_data
from concall_analyzer import get_concall_analysis
from llm_engine import get_llm_comparison

app = FastAPI(title="Indian Equities Analysis Agent")

# Cache with 1 hour TTL (3600 seconds), max 100 entries
analysis_cache = TTLCache(maxsize=100, ttl=3600)

class AnalysisRequest(BaseModel):
    symbol: str
    period: str = "1y"

@app.get("/")
def read_root():
    return {"message": "Indian Equities Analysis Agent API is running"}

@app.get("/analyze/{symbol}")
def analyze_stock(symbol: str, period: str = "max"):
    """
    Full analysis endpoint: Data + Technicals + Fundamentals
    """
    # Check cache first
    cache_key = f"{symbol}_{period}"
    if cache_key in analysis_cache:
        print(f"Cache hit for {symbol}")
        return analysis_cache[cache_key]
    
    print(f"Cache miss for {symbol}, fetching fresh data...")
    
    # 1. Fetch Data
    try:
        data = get_stock_data(symbol, period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    
    history = data["history"]
    info = data["info"]
    
    if history.empty:
        raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

    # 2. Technical Analysis
    try:
        tech_df = calculate_technicals(history)
        # Get the latest indicators (last row)
        latest_tech = tech_df.iloc[-1].to_dict()
        
        # Convert Timestamp objects to strings for JSON serialization
        latest_tech = {k: (v.isoformat() if isinstance(v, pd.Timestamp) else v) for k, v in latest_tech.items()}
        
        # Clean up NaN values for JSON
        latest_tech = {k: (None if pd.isna(v) else v) for k, v in latest_tech.items()}
        
    except Exception as e:
        latest_tech = {"error": str(e)}

    # 3. Fundamental Analysis
    try:
        fund_metrics = extract_fundamentals(info)
        fund_analysis = analyze_fundamentals(fund_metrics)
    except Exception as e:
        fund_metrics = {}
        fund_analysis = {"error": str(e)}

    # 4. Scrape additional data from Screener.in
    try:
        screener_data = scrape_screener_data(symbol)
    except Exception as e:
        screener_data = {"error": str(e)}

    # 5. Get concall analysis (async, may take time)
    try:
        concall_analysis = get_concall_analysis(symbol)
    except Exception as e:
        concall_analysis = {"status": "error", "error": str(e)}

    # 6. Get LLM comparison (Gemini vs Claude)
    try:
        llm_comparison = get_llm_comparison(symbol, latest_tech, {"metrics": fund_metrics}, screener_data, concall_analysis)
    except Exception as e:
        llm_comparison = {"error": str(e)}

    # 7. Calculate overall score
    try:
        score_result = calculate_score(latest_tech, {
            "metrics": fund_metrics,
            "analysis": fund_analysis
        }, screener_data)
    except Exception as e:
        score_result = {"error": str(e)}

    # Build response
    result = {
        "symbol": symbol.upper(),
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "symbol": symbol.upper(),
            "price": latest_tech.get("Close"),
            "score": score_result.get("score"),
            "verdict": score_result.get("verdict"),
            "technical_score": score_result.get("technical_score"),
            "fundamental_score": score_result.get("fundamental_score"),
            "timestamp": latest_tech.get("Date") or latest_tech.get("name")
        },
        "technicals": latest_tech,
        "fundamentals": {
            "metrics": fund_metrics,
            "analysis": fund_analysis
        },
        "screener_metrics": screener_data,
        "concall_analysis": concall_analysis,
        "llm_comparison": llm_comparison,
        "scoring_breakdown": scoring_result
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
