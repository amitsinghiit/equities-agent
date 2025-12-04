import streamlit as st
import pandas as pd
import requests
from thefuzz import process
import io
import os
import json

# Constants
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
NSE_EQUITY_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

st.set_page_config(page_title="Indian Equities Analysis Agent", layout="wide", page_icon="📈")

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Card Container */
    .custom-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
    
    /* Metrics */
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .metric-delta {
        font-size: 0.9rem;
        font-weight: 500;
    }
    .text-green { color: #4ade80; }
    .text-red { color: #f87171; }
    .text-yellow { color: #facc15; }
    .text-blue { color: #60a5fa; }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .badge-nse { background-color: #334155; color: #cbd5e1; }
    .badge-live { background-color: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6; }
    
    /* Score Cards */
    .score-card {
        background-color: #0f172a;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #1e293b;
        text-align: center;
    }
    
    /* Rationale Lists */
    .rationale-list {
        list-style-type: none;
        padding: 0;
    }
    .rationale-item {
        margin-bottom: 8px;
        display: flex;
        align-items: start;
        font-size: 0.9rem;
        color: #cbd5e1;
    }
    .rationale-icon {
        margin-right: 8px;
        font-size: 1rem;
    }
    
    /* Tables */
    .dataframe {
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
    }
    
    /* Progress Bar */
    .progress-container {
        width: 100%;
        background-color: #334155;
        border-radius: 9999px;
        height: 12px;
        overflow: hidden;
        display: flex;
        margin: 10px 0;
    }
    .progress-bar {
        height: 100%;
    }
    
    /* Concall Quote */
    .quote-box {
        background-color: #0f172a;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        font-style: italic;
        color: #cbd5e1;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* AI Comparison */
    .ai-card {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
    }
    .ai-gemini { border-top: 4px solid #3b82f6; }
    .ai-claude { border-top: 4px solid #a855f7; }
    
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_stock_list():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(NSE_EQUITY_URL, headers=headers)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        return df
    except Exception as e:
        st.error(f"Error fetching stock list: {e}")
        return pd.DataFrame()

def get_symbol_from_name(query, df):
    if df.empty: return None, None
    name_map = dict(zip(df['NAME OF COMPANY'], df['SYMBOL']))
    symbol_map = dict(zip(df['SYMBOL'], df['NAME OF COMPANY']))
    
    query_upper = query.upper().strip()
    if query_upper in symbol_map: return symbol_map[query_upper], query_upper
    
    for name in name_map:
        if name.upper().startswith(query_upper): return name, name_map[name]

    names = list(name_map.keys())
    best_match_name, score_name = process.extractOne(query, names)
    
    symbols = list(symbol_map.keys())
    best_match_symbol, score_symbol = process.extractOne(query_upper, symbols)
    
    if score_symbol > score_name:
        if score_symbol > 80: return symbol_map[best_match_symbol], best_match_symbol
    else:
        if score_name > 70: return best_match_name, name_map[best_match_name]
            
    return None, None

def analyze_stock(symbol):
    try:
        api_symbol = f"{symbol}.NS" if not symbol.endswith((".NS", ".BO")) else symbol
        with st.spinner(f"Analyzing {api_symbol}..."):
            response = requests.get(f"{BACKEND_URL}/analyze/{api_symbol}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        st.error(f"Error communicating with backend: {e}")
        return None

# --- UI Components ---

def render_header(data, symbol):
    summary = data.get("summary", {})
    screener = data.get("screener_metrics", {})
    top_ratios = screener.get("top_ratios", {})
    
    current_price = top_ratios.get("Current Price", "N/A")
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
            <h1 style="margin:0;">{symbol} <span class="badge badge-nse">NSE</span></h1>
            <p style="color: #94a3b8; margin:0;">{summary.get('symbol', symbol)}</p>
        </div>
        <div style="text-align: right;">
            <h1 style="margin:0;">{current_price}</h1>
            <span class="badge badge-live">Live Analysis</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_score_cards(data):
    summary = data.get("summary", {})
    score = summary.get('score', 0)
    verdict = summary.get('verdict', 'Neutral')
    tech_score = summary.get('technical_score', 0)
    
    verdict_color = "#facc15" # Yellow
    if verdict in ["Must Buy", "Should Buy"]: verdict_color = "#4ade80" # Green
    elif verdict == "Not a Buy": verdict_color = "#f87171" # Red
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="custom-card score-card">
            <div class="metric-label">Overall Score</div>
            <div class="metric-value" style="color: #60a5fa;">{score}/10</div>
            <div style="font-size: 0.8rem; color: #64748b;">Based on technicals & fundamentals</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="custom-card score-card">
            <div class="metric-label">Verdict</div>
            <div class="metric-value" style="color: {verdict_color};">{verdict}</div>
            <div style="font-size: 0.8rem; color: #64748b;">AI Recommendation</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="custom-card score-card">
            <div class="metric-label">Technical Score</div>
            <div class="metric-value" style="color: #f87171;">{tech_score}/5</div>
            <div style="font-size: 0.8rem; color: #64748b;">Short-term momentum</div>
        </div>
        """, unsafe_allow_html=True)

def render_rationale(data):
    reasons = data.get("scoring_breakdown", {}).get("reasons", [])
    positive = [r.replace("✅", "").strip() for r in reasons if "✅" in r]
    negative = [r.replace("❌", "").strip() for r in reasons if "❌" in r]
    warnings = [r.replace("⚠️", "").strip() for r in reasons if "⚠️" in r]
    
    # Merge warnings into negative for cleaner UI like mockup
    negative.extend(warnings)
    
    st.markdown("### Score Breakdown & Rationale")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="custom-card" style="border-left: 4px solid #4ade80;">
            <h4 style="color: #4ade80; margin-top:0;">✅ Strengths</h4>
        """, unsafe_allow_html=True)
        for p in positive:
            st.markdown(f"<div class='rationale-item'><span class='rationale-icon' style='color:#4ade80;'>•</span> {p}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="custom-card" style="border-left: 4px solid #f87171;">
            <h4 style="color: #f87171; margin-top:0;">⚠️ Weaknesses/Risks</h4>
        """, unsafe_allow_html=True)
        for n in negative:
            st.markdown(f"<div class='rationale-item'><span class='rationale-icon' style='color:#f87171;'>•</span> {n}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_technicals(data):
    tech = data.get("technicals", {})
    st.markdown("### Technical Indicators")
    
    cols = st.columns(6)
    
    metrics = [
        ("RSI (14)", f"{tech.get('RSI_14', 0):.2f}", "Neutral Zone"),
        ("MACD", f"{tech.get('MACD_12_26_9', 0):.2f}", f"Signal: {tech.get('MACDs_12_26_9', 0):.2f}"),
        ("200W EMA", f"{tech.get('EMA_200_Week', 0):.2f}", ""),
        ("SMA (50)", f"{tech.get('SMA_50', 0):.2f}", ""),
        ("SMA (200)", f"{tech.get('SMA_200', 0):.2f}", ""),
        ("BOLL LOWER", f"{tech.get('BBL_5_2.0', 0):.2f}", "")
    ]
    
    for i, (label, val, sub) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="custom-card" style="padding: 15px; text-align: center; min-height: 120px;">
                <div class="metric-label" style="font-size: 0.7rem;">{label}</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #f8fafc;">{val}</div>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 5px;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

def render_growth_metrics(data):
    screener = data.get("screener_metrics", {})
    st.markdown("### Growth Metrics (Consolidated)")
    
    sales = screener.get('compounded_sales_growth', {})
    profit = screener.get('compounded_profit_growth', {})
    cagr = screener.get('stock_price_cagr', {})
    roe = screener.get('return_on_equity', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Compounded Sales Growth**")
        if sales:
            df = pd.DataFrame(list(sales.items()), columns=["Period", "Growth %"])
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("N/A")

    with col2:
        st.markdown("**Compounded Profit Growth**")
        if profit:
            df = pd.DataFrame(list(profit.items()), columns=["Period", "Growth %"])
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("N/A")

    with col3:
        st.markdown("**Stock Price CAGR**")
        if cagr:
            df = pd.DataFrame(list(cagr.items()), columns=["Period", "CAGR %"])
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("N/A")

    with col4:
        st.markdown("**Return on Equity**")
        if roe:
            df = pd.DataFrame(list(roe.items()), columns=["Period", "ROE %"])
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("N/A")

def render_shareholding(data):
    screener = data.get("screener_metrics", {})
    shp = screener.get('shareholding_pattern', {})
    
    if not shp: return
    
    st.markdown("### Shareholding Pattern")
    st.markdown("<p style='color:#94a3b8; font-size: 0.9rem;'>Last 12 quarters trend</p>", unsafe_allow_html=True)
    
    # Table
    quarters = shp.get('quarters', [])
    shp_data = shp.get('data', {})
    
    df_shp = pd.DataFrame(shp_data)
    if len(quarters) == len(df_shp):
        df_shp.index = quarters
        df_shp = df_shp.T
        if len(df_shp.columns) > 12: df_shp = df_shp.iloc[:, -12:]
        st.dataframe(df_shp, use_container_width=True)
    
    # QoQ Analysis Visual
    if len(quarters) >= 2:
        latest_q = quarters[-1]
        prev_q = quarters[-2]
        
        st.markdown(f"#### QoQ Shareholding Analysis ({latest_q})")
        
        # Calculate percentages for progress bar
        try:
            promoters = float(shp_data.get('Promoters', ['0'])[-1].replace('%', ''))
            fiis = float(shp_data.get('FIIs', ['0'])[-1].replace('%', ''))
            diis = float(shp_data.get('DIIs', ['0'])[-1].replace('%', ''))
            public = float(shp_data.get('Public', ['0'])[-1].replace('%', ''))
            
            total = promoters + fiis + diis + public
            # Normalize if needed, but usually sums to 100
            
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-bar" style="width: {promoters}%; background-color: #3b82f6;"></div>
                <div class="progress-bar" style="width: {fiis}%; background-color: #0ea5e9;"></div>
                <div class="progress-bar" style="width: {diis}%; background-color: #22c55e;"></div>
                <div class="progress-bar" style="width: {public}%; background-color: #f59e0b;"></div>
            </div>
            <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; font-size: 0.8rem; color: #cbd5e1; margin-bottom: 20px;">
                <div style="display: flex; align-items: center;"><span style="width: 10px; height: 10px; background-color: #3b82f6; border-radius: 50%; margin-right: 5px;"></span> Promoters {promoters}%</div>
                <div style="display: flex; align-items: center;"><span style="width: 10px; height: 10px; background-color: #0ea5e9; border-radius: 50%; margin-right: 5px;"></span> FIIs {fiis}%</div>
                <div style="display: flex; align-items: center;"><span style="width: 10px; height: 10px; background-color: #22c55e; border-radius: 50%; margin-right: 5px;"></span> DIIs {diis}%</div>
                <div style="display: flex; align-items: center;"><span style="width: 10px; height: 10px; background-color: #f59e0b; border-radius: 50%; margin-right: 5px;"></span> Public {public}%</div>
            </div>
            """, unsafe_allow_html=True)
            
        except:
            pass

def render_fundamentals(data):
    screener = data.get("screener_metrics", {})
    top_ratios = screener.get('top_ratios', {})
    
    st.markdown("### Fundamental Data (Consolidated)")
    
    if top_ratios:
        cols = st.columns(5)
        metrics = list(top_ratios.items())
        
        for i, (label, val) in enumerate(metrics):
            with cols[i % 5]:
                st.markdown(f"""
                <div class="custom-card" style="padding: 15px; min-height: 100px;">
                    <div class="metric-label">{label}</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc;">{val}</div>
                </div>
                """, unsafe_allow_html=True)

def render_concall(data):
    concall = data.get("concall_analysis", {})
    if not concall or concall.get("status") != "success": return
    
    st.markdown("### Latest Concall Analysis")
    st.markdown("<p style='color:#94a3b8; font-size: 0.9rem;'>AI-powered analysis of recent investor presentation</p>", unsafe_allow_html=True)
    
    summary = concall.get("summary", "")
    
    st.markdown(f"""
    <div class="custom-card">
        <h4 style="color: #facc15; margin-top:0;">⚡ Key Business Highlights</h4>
        <div style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;">
            {summary.replace(chr(10), '<br>')}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_llm_comparison(data):
    llm = data.get("llm_comparison", {})
    if not llm: return
    
    st.markdown("### AI Model Comparison (Gemini vs Claude)")
    
    col1, col2 = st.columns(2)
    
    gemini = llm.get("gemini", {})
    claude = llm.get("claude", {})
    
    with col1:
        st.markdown(f"""
        <div class="ai-card ai-gemini">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <span style="font-size: 1.5rem; margin-right: 10px;">🔵</span>
                <h3 style="margin:0;">Gemini 2.0 Flash</h3>
            </div>
            <div style="margin-bottom: 15px;">
                <span class="metric-label">Verdict</span>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">{gemini.get('verdict', 'N/A')}</div>
            </div>
            <div style="margin-bottom: 15px;">
                <span class="metric-label">Score</span>
                <div style="font-size: 1.5rem; font-weight: 700; color: #60a5fa;">{gemini.get('score', 'N/A')}/10</div>
            </div>
            <div style="background: #1e293b; padding: 15px; border-radius: 8px; font-size: 0.9rem; color: #cbd5e1;">
                {gemini.get('summary', 'No summary available.')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        error_msg = claude.get('error', '')
        content = f"<div style='color: #f87171;'>{error_msg}</div>" if error_msg else claude.get('summary', 'No summary available.')
        verdict = claude.get('verdict', 'N/A') if not error_msg else "Error"
        score = f"{claude.get('score', 'N/A')}/10" if not error_msg else "N/A"
        
        st.markdown(f"""
        <div class="ai-card ai-claude">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <span style="font-size: 1.5rem; margin-right: 10px;">🟣</span>
                <h3 style="margin:0;">Claude 3.5 Sonnet</h3>
            </div>
            <div style="margin-bottom: 15px;">
                <span class="metric-label">Verdict</span>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">{verdict}</div>
            </div>
            <div style="margin-bottom: 15px;">
                <span class="metric-label">Score</span>
                <div style="font-size: 1.5rem; font-weight: 700; color: #a855f7;">{score}</div>
            </div>
            <div style="background: #1e293b; padding: 15px; border-radius: 8px; font-size: 0.9rem; color: #cbd5e1;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Main App Logic ---

st.title("🇮🇳 Indian Equities Analysis Agent")
st.markdown("Enter a company name to analyze its technicals and fundamentals.")

df_stocks = load_stock_list()

if not df_stocks.empty:
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Company Name", placeholder="e.g., Reliance, Tata Motors, Infosys")
    
    if query:
        match_name, match_symbol = get_symbol_from_name(query, df_stocks)
        
        if match_name:
            st.success(f"Found: **{match_name}** ({match_symbol})")
            
            if st.button("Analyze Stock", type="primary"):
                data = analyze_stock(match_symbol)
                
                if data:
                    st.divider()
                    render_header(data, match_symbol)
                    render_score_cards(data)
                    render_rationale(data)
                    st.markdown("---")
                    render_technicals(data)
                    st.markdown("---")
                    render_growth_metrics(data)
                    st.markdown("---")
                    render_shareholding(data)
                    st.markdown("---")
                    render_fundamentals(data)
                    st.markdown("---")
                    render_concall(data)
                    st.markdown("---")
                    render_llm_comparison(data)
                    
        else:
            st.warning("No matching company found.")
else:
    st.error("Failed to load stock list.")
