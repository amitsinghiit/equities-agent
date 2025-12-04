import pandas as pd
import pandas_ta_classic as ta

def calculate_technicals(df: pd.DataFrame):
    """
    Calculates technical indicators using pandas-ta.
    Expects a DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume'.
    """
    if df.empty:
        return df
    
    # Make a copy to avoid SettingWithCopy warnings on the original df if needed
    df = df.copy()
    
    # SMA
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    
    # RSI
    df.ta.rsi(length=14, append=True)
    
    # MACD
    df.ta.macd(append=True)
    
    # Bollinger Bands
    df.ta.bbands(append=True)

    # 200 Week EMA
    # Resample to weekly, calc EMA, then merge back or just take the last value
    # We need to be careful with merging back to daily timeframe if we want a series, 
    # but for "latest" value, we can just calc on weekly.
    weekly_df = df.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    # Calculate 200 EMA on weekly Close prices
    weekly_ema = weekly_df['Close'].ewm(span=200, adjust=False).mean()
    
    # We want to attach the latest weekly EMA to the daily dataframe (or at least the last row)
    # Forward fill the weekly EMA to daily dates
    weekly_ema_series = weekly_ema.reindex(df.index, method='ffill')
    df['EMA_200_Week'] = weekly_ema_series

    return df
