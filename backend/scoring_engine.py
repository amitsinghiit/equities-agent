import pandas as pd
from typing import Dict, Any

def parse_screener_value(value_str: str) -> float:
    """Parse string values from Screener (e.g., '1,234 Cr.', '12.5 %') to float."""
    if not value_str or not isinstance(value_str, str):
        return None
    try:
        # Remove commas, %, Cr., and whitespace
        clean_val = value_str.replace(',', '').replace('%', '').replace('Cr.', '').strip()
        return float(clean_val)
    except ValueError:
        return None

def calculate_score(technicals: Dict[str, Any], fundamentals: Dict[str, Any], screener_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Calculate a comprehensive score (1-10) based on technical and fundamental indicators.
    Prioritizes Screener.in data for fundamentals if available.
    """
    
    technical_score = 0
    fundamental_score = 0
    
    reasons = []
    
    # === TECHNICAL SCORING (0-5 points) ===
    
    # 1. RSI Analysis (0-1 points)
    rsi = technicals.get('RSI_14')
    if rsi:
        if 30 <= rsi <= 50:
            technical_score += 1
            reasons.append("✅ RSI is in optimal buying zone (30-50)")
        elif 50 < rsi <= 60:
            technical_score += 0.7
            reasons.append("✅ RSI indicates slightly bullish momentum")
        elif 60 < rsi <= 70:
            technical_score += 0.3
            reasons.append("⚠️ RSI is approaching overbought levels")
        elif rsi < 30:
            technical_score += 0.5
            reasons.append("⚠️ RSI is very oversold (<30), potential rebound")
        else:
            reasons.append("❌ RSI indicates overbought conditions (>70)")
    
    # 2. MACD Analysis (0-1 points)
    macd = technicals.get('MACD_12_26_9')
    macd_signal = technicals.get('MACDs_12_26_9')
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            technical_score += 1
            reasons.append("✅ MACD is above signal line (Bullish Crossover)")
        elif macd > macd_signal * 0.95:
            technical_score += 0.5
            reasons.append("⚠️ MACD is close to crossover")
        else:
            reasons.append("❌ MACD is below signal line (Bearish)")
    
    # 3. Moving Averages (0-1.5 points)
    close = technicals.get('Close')
    sma_50 = technicals.get('SMA_50')
    sma_200 = technicals.get('SMA_200')
    ema_200_week = technicals.get('EMA_200_Week')
    
    if close and sma_50 and sma_200:
        if sma_50 > sma_200:
            technical_score += 0.5
            reasons.append("✅ Golden Cross active (50 SMA > 200 SMA)")
        else:
            reasons.append("❌ Death Cross active (50 SMA < 200 SMA)")
        
        if close > sma_50:
            technical_score += 0.5
            reasons.append("✅ Price is above 50-day SMA")
        else:
            reasons.append("❌ Price is below 50-day SMA")
        
        if close > sma_200:
            technical_score += 0.25
            reasons.append("✅ Price is above 200-day SMA")
        else:
            reasons.append("❌ Price is below 200-day SMA")
    
    # 4. 200 Week EMA (0-0.5 points)
    if close and ema_200_week:
        if close > ema_200_week:
            technical_score += 0.5
            reasons.append("✅ Price is above long-term 200-week EMA")
        elif close > ema_200_week * 0.95:
            technical_score += 0.25
            reasons.append("⚠️ Price is near long-term 200-week EMA support")
        else:
            reasons.append("❌ Price is below long-term 200-week EMA")
    
    # 5. Bollinger Bands (0-1 points)
    bbl = technicals.get('BBL_5_2.0')
    bbu = technicals.get('BBU_5_2.0')
    
    if close and bbl and bbu:
        bb_position = (close - bbl) / (bbu - bbl) if (bbu - bbl) != 0 else 0.5
        if 0.2 <= bb_position <= 0.5:
            technical_score += 1
            reasons.append("✅ Price is in lower Bollinger Band zone (Potential Buy)")
        elif 0.5 < bb_position <= 0.7:
            technical_score += 0.5
            reasons.append("⚠️ Price is in middle Bollinger Band zone")
        elif bb_position > 0.8:
             reasons.append("❌ Price is near upper Bollinger Band (Potential Resistance)")
    
    # === FUNDAMENTAL SCORING (0-5 points) ===
    
    # Get Screener Data if available
    top_ratios = screener_data.get('top_ratios', {}) if screener_data else {}
    
    # Fallback to yfinance data
    fund_metrics = fundamentals.get('metrics', {})
    valuation = fund_metrics.get('valuation', {})
    performance = fund_metrics.get('performance', {})
    financial_health = fund_metrics.get('financial_health', {})
    growth = fund_metrics.get('growth', {})
    
    # 1. P/E Ratio (0-1 points)
    # Try Screener first (Stock P/E)
    pe_ratio = parse_screener_value(top_ratios.get('Stock P/E'))
    if pe_ratio is None:
        pe_ratio = valuation.get('pe_ratio')
        
    if pe_ratio:
        if 10 <= pe_ratio <= 25:
            fundamental_score += 1
            reasons.append(f"✅ P/E Ratio is attractive ({pe_ratio:.1f})")
        elif 25 < pe_ratio <= 35:
            fundamental_score += 0.5
            reasons.append(f"⚠️ P/E Ratio is slightly elevated ({pe_ratio:.1f})")
        elif pe_ratio < 10:
            fundamental_score += 0.7
            reasons.append(f"✅ P/E Ratio is very low ({pe_ratio:.1f})")
        else:
            reasons.append(f"❌ P/E Ratio is high ({pe_ratio:.1f})")
    
    # 2. Market Cap (0-0.5 points)
    # Try Screener first (Market Cap)
    market_cap = parse_screener_value(top_ratios.get('Market Cap'))
    if market_cap is not None:
        # Screener Market Cap is usually in Cr.
        # Actually, let's just use Cr thresholds for Screener data
        if market_cap > 100000: # > 1 Lakh Cr
             fundamental_score += 0.5
             reasons.append("✅ Large Cap company (>1L Cr) - High Stability")
        elif market_cap > 10000: # > 10k Cr
             fundamental_score += 0.3
             reasons.append("✅ Mid Cap company (>10k Cr) - Moderate Stability")
    else:
        # Fallback to yfinance (Market Cap is in actual currency)
        market_cap = valuation.get('market_cap')
        if market_cap:
            if market_cap > 100_000_000_000:
                fundamental_score += 0.5
                reasons.append("✅ Large Cap company (>100B) - High Stability")
            elif market_cap > 10_000_000_000:
                fundamental_score += 0.3
                reasons.append("✅ Mid Cap company (>10B) - Moderate Stability")
    
    # 3. Dividend Yield (0-0.5 points)
    div_yield = parse_screener_value(top_ratios.get('Dividend Yield'))
    if div_yield is None:
        div_yield = valuation.get('dividend_yield')
        if div_yield: div_yield = div_yield * 100 # Convert decimal to % for yfinance
    
    if div_yield:
        if div_yield > 2.0:
            fundamental_score += 0.5
            reasons.append(f"✅ Good Dividend Yield ({div_yield:.2f}%)")
        elif div_yield > 1.0:
            fundamental_score += 0.25
            reasons.append(f"✅ Moderate Dividend Yield ({div_yield:.2f}%)")
    
    # 4. Profit Margins / ROCE (0-1 points)
    # Screener gives ROCE/ROE which are better indicators than just profit margin
    roce = parse_screener_value(top_ratios.get('ROCE'))
    roe = parse_screener_value(top_ratios.get('ROE'))
    
    if roce and roe:
        if roce > 20 and roe > 20:
             fundamental_score += 1
             reasons.append(f"✅ Excellent Return Ratios (ROCE: {roce}%, ROE: {roe}%)")
        elif roce > 15 and roe > 15:
             fundamental_score += 0.7
             reasons.append(f"✅ Healthy Return Ratios (ROCE: {roce}%, ROE: {roe}%)")
        elif roce < 10 or roe < 10:
             reasons.append(f"⚠️ Low Return Ratios (ROCE: {roce}%, ROE: {roe}%)")
    else:
        # Fallback to Profit Margin from yfinance
        profit_margin = performance.get('profit_margin')
        if profit_margin:
            if profit_margin > 0.15:
                fundamental_score += 1
                reasons.append("✅ Strong Profit Margins (>15%)")
            elif profit_margin > 0.10:
                fundamental_score += 0.7
                reasons.append("✅ Healthy Profit Margins (>10%)")
            elif profit_margin > 0.05:
                fundamental_score += 0.4
                reasons.append("⚠️ Low Profit Margins (5-10%)")
            else:
                reasons.append("❌ Very Low Profit Margins (<5%)")

    # 5. Revenue/Profit Growth (0-1 points)
    # Screener doesn't give growth in top_ratios usually, unless customized. 
    # We'll stick to yfinance for growth OR check if we scraped it elsewhere.
    # Actually we scrape 'compounded_sales_growth' in screener_scraper.
    sales_growth_3yr = None
    if screener_data and 'compounded_sales_growth' in screener_data:
        # Try to get '3 Years' or 'TTM'
        sg = screener_data['compounded_sales_growth']
        val_str = sg.get('3 Years') or sg.get('TTM')
        sales_growth_3yr = parse_screener_value(val_str)
    
    if sales_growth_3yr is not None:
        if sales_growth_3yr > 20:
            fundamental_score += 1
            reasons.append(f"✅ Excellent Sales Growth ({sales_growth_3yr}%)")
        elif sales_growth_3yr > 10:
            fundamental_score += 0.7
            reasons.append(f"✅ Good Sales Growth ({sales_growth_3yr}%)")
        elif sales_growth_3yr > 5:
            fundamental_score += 0.4
            reasons.append(f"⚠️ Slow Sales Growth ({sales_growth_3yr}%)")
        elif sales_growth_3yr < 0:
            fundamental_score -= 0.5
            reasons.append(f"❌ Negative Sales Growth ({sales_growth_3yr}%)")
    else:
        # Fallback to yfinance
        revenue_growth = growth.get('revenue_growth')
        if revenue_growth:
            if revenue_growth > 0.20:
                fundamental_score += 1
                reasons.append("✅ Excellent Revenue Growth (>20%)")
            elif revenue_growth > 0.10:
                fundamental_score += 0.7
                reasons.append("✅ Good Revenue Growth (>10%)")
            elif revenue_growth > 0.05:
                fundamental_score += 0.4
                reasons.append("⚠️ Slow Revenue Growth (5-10%)")
            elif revenue_growth < 0:
                fundamental_score -= 0.5
                reasons.append("❌ Negative Revenue Growth")

    # 6. Debt to Equity (0-1 points)
    # Try Screener first
    debt_equity = parse_screener_value(top_ratios.get('Debt to equity'))
    if debt_equity is None:
        debt_to_equity = financial_health.get('debt_to_equity') # yfinance
    else:
        debt_to_equity = debt_equity

    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            fundamental_score += 1
            reasons.append(f"✅ Low Debt to Equity ({debt_to_equity:.2f})")
        elif debt_to_equity < 1.0:
            fundamental_score += 0.6
            reasons.append(f"✅ Moderate Debt to Equity ({debt_to_equity:.2f})")
        elif debt_to_equity < 2.0:
            fundamental_score += 0.3
            reasons.append(f"⚠️ High Debt to Equity ({debt_to_equity:.2f})")
        else:
            reasons.append(f"❌ Very High Debt ({debt_to_equity:.2f})")
    
    # Calculate final score (out of 10)
    total_score = technical_score + fundamental_score
    
    # Normalize to 1-10 scale
    normalized_score = min(10, max(1, total_score))
    
    # Determine verdict
    if normalized_score >= 9:
        verdict = "Must Buy"
    elif normalized_score >= 7:
        verdict = "Should Buy"
    elif normalized_score >= 6:
        verdict = "Buy"
    elif normalized_score >= 3:
        verdict = "Neutral"
    else:
        verdict = "Not a Buy"
    
    return {
        "score": round(normalized_score, 2),
        "verdict": verdict,
        "technical_score": round(technical_score, 2),
        "fundamental_score": round(fundamental_score, 2),
        "reasons": reasons,
        "breakdown": {
            "technical_max": 5.0,
            "fundamental_max": 5.0,
            "total_max": 10.0
        }
    }
