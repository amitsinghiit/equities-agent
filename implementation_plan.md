# Indian Equities Analysis Agent - Implementation Plan

## Objective
Build an AI Agent capable of performing Fundamental and Technical analysis on Indian equities (NSE/BSE).

## Core Capabilities

### 1. Data Acquisition
*   **Source**: `yfinance` (Yahoo Finance) for historical price data and basic financials.
*   **Source**: `nsetools` or direct scraping (e.g., Screener.in, NSE India) for deeper fundamental metrics if needed.
*   **Market**: Indian Stock Market (NSE symbols with `.NS` suffix).

### 2. Technical Analysis (Short/Medium Term)
*   **Trend Indicators**: Moving Averages (SMA 50, SMA 200), EMA.
*   **Momentum Indicators**: RSI (Relative Strength Index), MACD (Moving Average Convergence Divergence).
*   **Volatility**: Bollinger Bands.
*   **Pattern Recognition**: Basic candlestick patterns (Doji, Hammer, Engulfing) - *Optional V2*.

### 3. Fundamental Analysis (Long Term)
*   **Valuation**: P/E Ratio, P/B Ratio, Dividend Yield.
*   **Performance**: ROE (Return on Equity), ROCE.
*   **Financial Health**: Debt-to-Equity ratio.
*   **Growth**: Revenue growth, Profit growth (YoY, QoQ).

### 4. Agent "Brain" (Synthesis)
*   Combine technical signals (Buy/Sell/Neutral) with fundamental health (Strong/Weak).
*   Generate a summary verdict.

## Architecture

### Backend (Python)
*   **Framework**: FastAPI (to serve the agent as an API).
*   **Libraries**: `yfinance`, `pandas`, `pandas-ta` (Technical Analysis), `beautifulsoup4` (if scraping needed).

### Frontend (Web UI)
*   **Framework**: Next.js (React) or simple HTML/JS.
*   **Features**:
    *   Search bar for Stock Symbol (e.g., "TATASTEEL").
    *   Dashboard showing Price Chart.
    *   Technical Gauge (Bearish <-> Bullish).
    *   Fundamental Scorecard.

## Step-by-Step Implementation Plan
1.  **Setup**: Initialize Python environment and install dependencies.
2.  **Data Module**: Create functions to fetch OHLCV data and financial info for Indian stocks.
3.  **Technical Engine**: Implement TA indicators using `pandas-ta`.
4.  **Fundamental Engine**: Implement key ratio extraction.
5.  **API Layer**: Expose these as REST endpoints.
6.  **UI Layer**: Build a modern interface to interact with the agent.
