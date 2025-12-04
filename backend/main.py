from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import pandas as pd
import json

# Import our engines
from data_engine import get_stock_data
from technical_engine import calculate_technicals
from fundamental_engine import extract_fundamentals, analyze_fundamentals
from scoring_engine import calculate_score
from screener_scraper import scrape_screener_data
from concall_analyzer import get_concall_analysis
from llm_engine import get_llm_comparison

app = FastAPI(title="Indian Equities Analysis Agent")

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
        concall_analysis = {"error": str(e), "status": "error"}

    # 6. Get LLM Comparison (Gemini vs Claude)
    try:
        llm_comparison = get_llm_comparison(symbol, latest_tech, {"metrics": fund_metrics}, screener_data, concall_analysis)
    except Exception as e:
        llm_comparison = {"error": str(e)}

    # 7. Calculate Score and Verdict (Rule-based)
    scoring_result = calculate_score(latest_tech, {
        "metrics": fund_metrics,
        "analysis": fund_analysis
    }, screener_data)
    
    summary = {
        "symbol": symbol.upper(),
        "price": latest_tech.get("Close"),
        "score": scoring_result["score"],
        "verdict": scoring_result["verdict"],
        "technical_score": scoring_result["technical_score"],
        "fundamental_score": scoring_result["fundamental_score"],
        "timestamp": latest_tech.get("Date") or latest_tech.get("name")
    }

    return {
        "summary": summary,
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
