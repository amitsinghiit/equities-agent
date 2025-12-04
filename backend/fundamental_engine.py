from typing import Dict, Any

def extract_fundamentals(info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts key fundamental metrics from the yfinance info dictionary.
    Handles missing keys gracefully.
    """
    if not info:
        return {}

    metrics = {
        "valuation": {
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "market_cap": info.get("marketCap"),
        },
        "performance": {
            "roe": info.get("returnOnEquity"),
            "roce": None,  # yfinance often lacks ROCE, might need calculation or alternative source
            "profit_margin": info.get("profitMargins"),
        },
        "financial_health": {
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
        },
        "growth": {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
        }
    }
    
    # Normalize None values or format percentages if needed
    # For now, we keep raw values as returned by yfinance
    
    return metrics

def analyze_fundamentals(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Basic rule-based analysis of fundamentals.
    Returns a 'health' summary (Strong, Neutral, Weak) for categories.
    """
    analysis = {}
    
    # Example Logic (Very basic)
    pe = metrics["valuation"].get("pe_ratio")
    if pe:
        if pe < 20:
            analysis["valuation"] = "Attractive"
        elif pe < 40:
            analysis["valuation"] = "Fair"
        else:
            analysis["valuation"] = "Expensive"
    else:
        analysis["valuation"] = "Unknown"

    # ROE
    roe = metrics["performance"].get("roe")
    if roe:
        if roe > 0.15: # 15%
            analysis["performance"] = "Strong"
        elif roe > 0.10:
            analysis["performance"] = "Moderate"
        else:
            analysis["performance"] = "Weak"
    else:
        analysis["performance"] = "Unknown"
        
    return analysis
