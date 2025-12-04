import streamlit as st
import pandas as pd
import requests
from thefuzz import process
import io

import os

# Constants
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
NSE_EQUITY_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

st.set_page_config(page_title="Indian Equities Analysis Agent", layout="wide")

@st.cache_data
def load_stock_list():
    """
    Fetches the list of equities from NSE and returns a DataFrame.
    """
    try:
        # NSE blocks requests without a user agent sometimes, so we add one
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(NSE_EQUITY_URL, headers=headers)
        response.raise_for_status()
        
        # Read CSV from content
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        return df
    except Exception as e:
        st.error(f"Error fetching stock list: {e}")
        return pd.DataFrame()

def get_symbol_from_name(query, df):
    """
    Uses fuzzy matching to find the best match for the company name.
    """
    if df.empty:
        return None, None
    
    # Create a dictionary of Name -> Symbol
    name_map = dict(zip(df['NAME OF COMPANY'], df['SYMBOL']))
    names = list(name_map.keys())
    
    # Fuzzy match
    best_match, score = process.extractOne(query, names)
    
    if score > 60: # Threshold
        return best_match, name_map[best_match]
    return None, None

def analyze_stock(symbol):
    """
    Calls the backend API to analyze the stock.
    """
    try:
        # Append .NS for NSE stocks if not present (yfinance convention)
        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
             # Assuming NSE for now as per the list source
            api_symbol = f"{symbol}.NS"
        else:
            api_symbol = symbol
            
        with st.spinner(f"Analyzing {api_symbol}..."):
            response = requests.get(f"{BACKEND_URL}/analyze/{api_symbol}")
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with backend: {e}")
        return None

# --- Main UI ---

st.title("🇮🇳 Indian Equities Analysis Agent")
st.markdown("Enter a company name to analyze its technicals and fundamentals.")

# Load data
df_stocks = load_stock_list()

if not df_stocks.empty:
    # Search Input
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Company Name", placeholder="e.g., Reliance, Tata Motors, Infosys")
    
    selected_symbol = None
    
    if query:
        match_name, match_symbol = get_symbol_from_name(query, df_stocks)
        
        if match_name:
            st.success(f"Found: **{match_name}** ({match_symbol})")
            selected_symbol = match_symbol
            
            # Analyze Button
            if st.button("Analyze Stock", type="primary"):
                data = analyze_stock(selected_symbol)
                
                if data:
                    # Display Results
                    st.divider()
                    
                    # Summary Section
                    summary = data.get("summary", {})
                    st.header(f"Analysis for {summary.get('symbol', selected_symbol)}")
                    
                    # Score display with color coding
                    score = summary.get('score', 0)
                    verdict = summary.get('verdict', 'N/A')
                    
                    # Color code based on score
                    # Score and Verdict
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Overall Score", f"{summary['score']}/10")
                    with col2:
                        verdict_color = {
                            "Must Buy": "🟢",
                            "Should Buy": "🟢", 
                            "Buy": "🟡",
                            "Neutral": "🟡",
                            "Not a Buy": "🔴"
                        }.get(summary['verdict'], "⚪")
                        st.metric("Verdict", f"{verdict_color} {summary['verdict']}")
                    with col3:
                        st.metric("Technical Score", f"{summary['technical_score']}/5")
                        st.metric("Fundamental Score", f"{summary['fundamental_score']}/5")
                    
                    # Score Rationale
                    scoring_breakdown = data.get("scoring_breakdown", {})
                    reasons = scoring_breakdown.get("reasons", [])
                    
                    if reasons:
                        with st.expander("📋 Score Breakdown & Rationale", expanded=True):
                            st.markdown("**Factors Contributing to the Score:**")
                            
                            # Separate into positive and negative
                            positive = [r for r in reasons if r.startswith("✅")]
                            warnings = [r for r in reasons if r.startswith("⚠️")]
                            negative = [r for r in reasons if r.startswith("❌")]
                            
                            col_left, col_right = st.columns(2)
                            
                            with col_left:
                                if positive:
                                    st.markdown("**Strengths:**")
                                    for reason in positive:
                                        st.markdown(f"- {reason}")
                                
                                if warnings:
                                    st.markdown("**⚠️ Caution Points:**")
                                    for reason in warnings:
                                        st.markdown(f"- {reason}")
                            
                            with col_right:
                                if negative:
                                    st.markdown("**❌ Weaknesses/Risks:**")
                                    for reason in negative:
                                        st.markdown(f"- {reason}")
                    else:
                        with st.expander("Score Breakdown"):
                            st.json(scoring_breakdown)
                        tech_score = summary.get('technical_score', 0)
                        fund_score = summary.get('fundamental_score', 0)
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Technical Score", f"{tech_score}/5.0")
                        col2.metric("Fundamental Score", f"{fund_score}/5.0")
                        
                        st.markdown("""
                        **Score Ranges:**
                        - 🔴 **1-3**: Not a Buy
                        - 🟠 **3-6**: Neutral
                        - 🟡 **6-7**: Buy
                        - 🟢 **7-8**: Should Buy
                        - 🟢 **9-10**: Must Buy
                        """)
                    
                    # Technicals Section
                    st.subheader("Technical Indicators")
                    tech = data.get("technicals", {})
                    if "error" in tech:
                        st.error(f"Technical Analysis Error: {tech['error']}")
                    else:
                        # Display key technicals with full names
                        # Create rows of 3 metrics
                        
                        # Row 1
                        r1c1, r1c2, r1c3 = st.columns(3)
                        r1c1.metric("Relative Strength Index (RSI 14)", f"{tech.get('RSI_14', 0):.2f}")
                        
                        macd_val = tech.get('MACD_12_26_9')
                        macd_signal = tech.get('MACDs_12_26_9')
                        r1c2.metric("Moving Average Convergence Divergence (MACD)", f"{macd_val:.2f}" if macd_val else "N/A", delta=f"Signal: {macd_signal:.2f}" if macd_signal else None)
                        
                        ema_200_week = tech.get('EMA_200_Week')
                        r1c3.metric("200 Weeks EMA", f"{ema_200_week:.2f}" if ema_200_week else "N/A")

                        # Row 2
                        r2c1, r2c2, r2c3 = st.columns(3)
                        
                        sma_50 = tech.get('SMA_50')
                        r2c1.metric("Simple Moving Average (50 Day)", f"{sma_50:.2f}" if sma_50 else "N/A")
                        
                        sma_200 = tech.get('SMA_200')
                        r2c2.metric("Simple Moving Average (200 Day)", f"{sma_200:.2f}" if sma_200 else "N/A")

                        # Bollinger Bands
                        bbl = tech.get('BBL_5_2.0') 
                        bbu = tech.get('BBU_5_2.0')
                        bbm = tech.get('BBM_5_2.0')
                        
                        # Check for standard 20 length if 5 is not there (pandas-ta default is 5? No, usually 20, but let's be safe)
                        # Actually, in technical_engine.py we just called df.ta.bbands(append=True). 
                        # pandas-ta default length is 5. So BBL_5_2.0 is likely correct.
                        
                        r2c3.metric("Bollinger Bands (Lower)", f"{bbl:.2f}" if bbl else "N/A", help=f"Upper: {bbu:.2f}, Middle: {bbm:.2f}" if bbu else None)

                        with st.expander("Full Technical Data (Raw)"):
                            st.json(tech)

                    # Growth Metrics Section (from Screener.in)
                    screener_data = data.get("screener_metrics", {})
                    if screener_data and "error" not in screener_data:
                        source = screener_data.get('source', 'Consolidated')
                        st.subheader(f"📈 Growth Metrics ({source})")
                        
                        # Create 4 columns for the 4 metric types
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown("**Compounded Sales Growth**")
                            sales_growth = screener_data.get('compounded_sales_growth', {})
                            if sales_growth:
                                df_sales = pd.DataFrame(list(sales_growth.items()), columns=['Period', 'Growth'])
                                st.dataframe(df_sales, hide_index=True, use_container_width=True)
                            else:
                                st.info("No data available")
                        
                        with col2:
                            st.markdown("**Compounded Profit Growth**")
                            profit_growth = screener_data.get('compounded_profit_growth', {})
                            if profit_growth:
                                df_profit = pd.DataFrame(list(profit_growth.items()), columns=['Period', 'Growth'])
                                st.dataframe(df_profit, hide_index=True, use_container_width=True)
                            else:
                                st.info("No data available")
                        
                        with col3:
                            st.markdown("**Stock Price CAGR**")
                            price_cagr = screener_data.get('stock_price_cagr', {})
                            if price_cagr:
                                df_cagr = pd.DataFrame(list(price_cagr.items()), columns=['Period', 'CAGR'])
                                st.dataframe(df_cagr, hide_index=True, use_container_width=True)
                            else:
                                st.info("No data available")
                        
                        with col4:
                            st.markdown("**Return on Equity**")
                            roe = screener_data.get('return_on_equity', {})
                            if roe:
                                df_roe = pd.DataFrame(list(roe.items()), columns=['Period', 'ROE'])
                                st.dataframe(df_roe, hide_index=True, use_container_width=True)
                            else:
                                st.info("No data available")

                    # Shareholding Pattern Section
                    shp = screener_data.get('shareholding_pattern', {})
                    if shp and 'quarters' in shp and 'data' in shp:
                        st.subheader("📊 Shareholding Pattern")
                        
                        quarters = shp['quarters']
                        shp_data = shp['data']
                        
                        # Create DataFrame
                        df_shp = pd.DataFrame(shp_data)
                        # Ensure quarters match data length
                        num_rows = len(df_shp)
                        current_quarters = quarters[:num_rows]
                        df_shp.index = current_quarters
                        
                        df_shp = df_shp.T # Transpose to have Quarters as columns
                        
                        # Slice to last 12 columns if needed
                        if len(df_shp.columns) > 12:
                            df_shp = df_shp.iloc[:, -12:]
                        
                        # Display the table (Last 12 quarters)
                        st.dataframe(df_shp, use_container_width=True)
                        
                        # Analysis of latest QoQ change
                        if len(quarters) >= 2:
                            latest_q = quarters[-1]
                            prev_q = quarters[-2]
                            
                            st.markdown(f"**QoQ Analysis ({prev_q} vs {latest_q})**")
                            
                            cols = st.columns(4)
                            
                            categories = [
                                ("Promoters", "Positive"), 
                                ("FIIs", "Positive"), 
                                ("DIIs", "Positive"), 
                                ("Public", "Negative")
                            ]
                            
                            for i, (cat, sentiment_type) in enumerate(categories):
                                if cat in shp_data:
                                    vals = shp_data[cat]
                                    if len(vals) >= 2:
                                        try:
                                            curr_val = float(vals[-1].replace('%', ''))
                                            prev_val = float(vals[-2].replace('%', ''))
                                            diff = curr_val - prev_val
                                            
                                            # Determine sentiment
                                            is_positive = False
                                            if sentiment_type == "Positive":
                                                is_positive = diff > 0
                                            else: # Negative sentiment type (Public)
                                                is_positive = diff < 0 # Decrease is good
                                            
                                            color = "green" if is_positive else "red"
                                            if diff == 0: color = "gray"
                                            
                                            with cols[i]:
                                                st.metric(
                                                    label=cat,
                                                    value=f"{curr_val}%",
                                                    delta=f"{diff:.2f}%",
                                                    delta_color="normal" if sentiment_type == "Positive" else "inverse"
                                                )
                                                if diff != 0:
                                                    significance = "Positive" if is_positive else "Negative"
                                                    st.markdown(f":{color}[{significance} Sign]")
                                                else:
                                                    st.markdown(":gray[Neutral]")
                                        except ValueError:
                                            pass

                    # Fundamental Data Section (Screener.in)
                    st.subheader(f"Fundamental Data ({screener_data.get('source', 'Screener.in')})")
                    
                    top_ratios = screener_data.get('top_ratios', {})
                    if top_ratios:
                        st.markdown("**Key Metrics (Current/TTM)**")
                        
                        # Create columns for metrics
                        # We'll display them in rows of 3 or 4
                        metrics_list = list(top_ratios.items())
                        
                        # Helper to chunks
                        def chunked(iterable, n):
                            return [iterable[i:i + n] for i in range(0, len(iterable), n)]
                        
                        for row_metrics in chunked(metrics_list, 4):
                            cols = st.columns(4)
                            for i, (name, value) in enumerate(row_metrics):
                                with cols[i]:
                                    st.metric(name, value)
                    else:
                        # Fallback to yfinance data if screener data is missing
                        fund = data.get("fundamentals", {})
                        fund_metrics = fund.get("metrics", {})
                        if fund_metrics:
                            st.json(fund_metrics)
                        else:
                            st.info("No fundamental data available.")

                    # Analysis from backend (still useful as it interprets the data)
                    fund_analysis = data.get("fundamentals", {}).get("analysis", {})
                    if fund_analysis and "error" not in fund_analysis:
                         st.markdown("### Analysis (Automated)")
                         st.write(fund_analysis)

                    # Concall Analysis Section
                    concall_data = data.get("concall_analysis", {})
                    if concall_data and concall_data.get("status") != "not_found":
                        st.subheader("📊 Latest Concall Analysis")
                        
                        if concall_data.get("status") == "success":
                            st.markdown("**AI-Powered Analysis of Recent Investor Presentation**")
                            st.markdown("*Source: Latest concall presentation from Screener.in, analyzed by Gemini AI*")
                            st.markdown("---")
                            
                            summary = concall_data.get("summary", "")
                            if summary:
                                # Display the summary in a nice format
                                st.markdown(summary)
                            else:
                                st.info("No summary available")
                        elif concall_data.get("status") == "error":
                            with st.expander("⚠️ Concall Analysis Error"):
                                st.error(f"Error: {concall_data.get('error', 'Unknown error')}")
                                st.info("This feature requires a Gemini API key. Please set the GEMINI_API_KEY environment variable.")
                        else:
                            st.info("Concall analysis is being processed...")
                    else:
                        st.info("💡 No recent concall presentation available for this company")

                    # AI Model Comparison Section
                    llm_comparison = data.get("llm_comparison", {})
                    if llm_comparison and "error" not in llm_comparison:
                        st.subheader("🤖 AI Model Comparison (Gemini vs Claude)")
                        
                        gemini = llm_comparison.get("gemini", {})
                        claude = llm_comparison.get("claude", {})
                        
                        # Check for errors in individual model responses
                        gemini_error = gemini.get("error")
                        claude_error = claude.get("error")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### 🔵 Gemini 2.0 Flash")
                            if gemini_error:
                                st.error(f"Error: {gemini_error}")
                            else:
                                st.metric("Verdict", gemini.get("verdict", "N/A"))
                                st.metric("Score", f"{gemini.get('score', 'N/A')}/10")
                                st.markdown("**Interpretation:**")
                                st.info(gemini.get("summary", "No summary provided."))
                        
                        with col2:
                            st.markdown("### 🟣 Claude 3.5 Sonnet")
                            if claude_error:
                                st.error(f"Error: {claude_error}")
                                if "Anthropic API Key not set" in str(claude_error):
                                    st.caption("Set ANTHROPIC_API_KEY to enable Claude analysis.")
                            else:
                                st.metric("Verdict", claude.get("verdict", "N/A"))
                                st.metric("Score", f"{claude.get('score', 'N/A')}/10")
                                st.markdown("**Interpretation:**")
                                st.info(claude.get("summary", "No summary provided."))

        else:
            st.warning("No matching company found. Please try a different name.")

else:
    st.error("Could not load stock list. Please check your internet connection or the data source.")
