import os
import json
import google.generativeai as genai
from anthropic import Anthropic
from typing import Dict, Any, Optional

# Configure APIs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_prompt(symbol: str, technicals: Dict, fundamentals: Dict, screener_data: Dict, concall_summary: str) -> str:
    """
    Generate a comprehensive prompt for the LLMs to analyze the stock.
    """
    
    # Format Technicals
    tech_str = json.dumps(technicals, indent=2)
    
    # Format Fundamentals
    fund_str = json.dumps(fundamentals.get('metrics', {}), indent=2)
    
    # Format Screener Data (Top Ratios & Shareholding)
    screener_str = json.dumps(screener_data, indent=2)
    
    prompt = f"""
You are an expert financial analyst. Analyze the following data for {symbol} and provide a verdict, score, and interpretation.

### 1. Technical Indicators
{tech_str}

### 2. Fundamental Metrics (yfinance)
{fund_str}

### 3. Key Metrics & Shareholding (Screener.in)
{screener_str}

### 4. Recent Concall/Presentation Summary
{concall_summary}

---

Based on ALL the above data, please provide a JSON response with the following fields:
1. "verdict": One of ["Must Buy", "Buy", "Hold", "Sell", "Avoid"]
2. "score": A score from 0 to 10 (10 being the best investment opportunity)
3. "summary": A concise 3-4 sentence interpretation of the company's outlook, citing specific reasons from the data (technicals, fundamentals, or concall).

**IMPORTANT**: Return ONLY the JSON object. Do not include markdown formatting like ```json ... ```.
Example format:
{{
  "verdict": "Buy",
  "score": 7.5,
  "summary": "The company shows strong fundamental growth with 20% revenue increase. Technicals are bullish with RSI at 45. Concall indicates positive future guidance."
}}
"""
    return prompt

def analyze_with_gemini(prompt: str) -> Dict[str, Any]:
    """
    Analyze stock data using Gemini.
    """
    if not GEMINI_API_KEY:
        return {"error": "Gemini API Key not set"}
        
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Clean response to ensure valid JSON
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text)
    except Exception as e:
        return {"error": f"Gemini Analysis Failed: {str(e)}"}

def analyze_with_claude(prompt: str) -> Dict[str, Any]:
    """
    Analyze stock data using Claude.
    """
    if not ANTHROPIC_API_KEY:
        return {"error": "Anthropic API Key not set"}
        
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            system="You are a financial analyst assistant that outputs strict JSON.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        text = message.content[0].text.strip()
        # Clean response
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text)
    except Exception as e:
        return {"error": f"Claude Analysis Failed: {str(e)}"}

def get_llm_comparison(symbol: str, technicals: Dict, fundamentals: Dict, screener_data: Dict, concall_analysis: Dict) -> Dict[str, Any]:
    """
    Get comparative analysis from both LLMs.
    """
    concall_summary = concall_analysis.get("summary", "No concall analysis available.")
    
    prompt = generate_prompt(symbol, technicals, fundamentals, screener_data, concall_summary)
    
    gemini_result = analyze_with_gemini(prompt)
    claude_result = analyze_with_claude(prompt)
    
    return {
        "gemini": gemini_result,
        "claude": claude_result
    }
