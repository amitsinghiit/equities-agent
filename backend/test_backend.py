import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_engine import get_stock_data
from technical_engine import calculate_technicals
from fundamental_engine import extract_fundamentals, analyze_fundamentals

def test_pipeline(symbol="TATASTEEL.NS"):
    print(f"Testing pipeline for {symbol}...")
    
    # 1. Data
    print("1. Fetching Data...")
    try:
        data = get_stock_data(symbol)
        history = data["history"]
        info = data["info"]
        print(f"   - History shape: {history.shape}")
        print(f"   - Info keys: {list(info.keys())[:5]}...")
    except Exception as e:
        print(f"   X Error fetching data: {e}")
        return

    # 2. Technicals
    print("2. Calculating Technicals...")
    try:
        tech_df = calculate_technicals(history)
        print(f"   - Columns: {tech_df.columns.tolist()}")
        print(f"   - Last RSI: {tech_df['RSI_14'].iloc[-1]}")
    except Exception as e:
        print(f"   X Error calculating technicals: {e}")

    # 3. Fundamentals
    print("3. Analyzing Fundamentals...")
    try:
        fund_metrics = extract_fundamentals(info)
        fund_analysis = analyze_fundamentals(fund_metrics)
        print(f"   - Metrics: {fund_metrics}")
        print(f"   - Analysis: {fund_analysis}")
    except Exception as e:
        print(f"   X Error analyzing fundamentals: {e}")

    print("Pipeline Test Complete.")

if __name__ == "__main__":
    test_pipeline()
