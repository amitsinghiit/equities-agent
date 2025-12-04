import yfinance as yf
import pandas as pd

def get_stock_data(symbol: str, period: str = "1y"):
    """
    Fetches historical data for an Indian stock.
    Appends .NS if not present and no suffix is provided.
    """
    symbol = symbol.upper()
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = f"{symbol}.NS"
    
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period)
    
    # Basic info
    try:
        info = ticker.info
    except Exception:
        info = {}
    
    return {
        "history": history,
        "info": info
    }
