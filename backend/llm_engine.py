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

### CRITICAL ANALYSIS FACTORS:
You MUST evaluate the company based on the following 5 specific factors:
1. **Sales & Profit Growth/Degrowth**: Analyze the historical growth trends (CAGR) and recent quarterly performance.
2. **Institutional Holding (FII/DII)**: Check for recent changes in FII/DII ownership. Increasing holding is positive, decreasing is negative.
3. **Management Projections**: Evaluate future guidance and outlook provided in the concall summary.
4. **Geo-Politics**: Use your knowledge to assess any geo-political risks or opportunities relevant to this specific sector.
5. **Regulatory Impact**: Consider any recent or upcoming government regulations that could impact this company or sector.

---

Based on ALL the above data and factors, please provide a JSON response with the following fields:
1. "verdict": One of ["Must Buy", "Buy", "Hold", "Sell", "Avoid"]
2. "score": A score from 0 to 10 (10 being the best investment opportunity)
3. "summary": A concise 3-4 sentence interpretation. You MUST explicitly mention the key drivers from the 5 factors above (e.g., "Despite strong growth, regulatory headwinds...")

**IMPORTANT**: Return ONLY the JSON object. Do not include markdown formatting like ```json ... ```.
Example format:
{{
  "verdict": "Buy",
  "score": 7.5,
  "summary": "The company shows strong 20% profit growth and increasing FII interest. Management projects double-digit growth, though geo-political tensions in Europe pose a slight risk to exports."
}}
"""
    return prompt

import time
import random

def analyze_with_gemini(prompt: str) -> Dict[str, Any]:
    """
    Analyze stock data using Gemini with retry logic for rate limits.
    """
    if not GEMINI_API_KEY:
        return {"error": "Gemini API Key not set"}
        
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            
            # Clean response to ensure valid JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text)
            
        except Exception as e:
            error_str = str(e)
            # Check for rate limit errors (429)
            if "429" in error_str or "Resource exhausted" in error_str:
                if attempt < max_retries - 1:
                    # Exponential backoff + jitter: 2s, 4s, 8s... + random
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"Gemini 429 error. Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
            
            # If it's not a rate limit or we ran out of retries
            return {"error": f"Gemini Analysis Failed: {error_str}"}
            
    return {"error": "Gemini Analysis Failed: Max retries exceeded"}

def analyze_with_claude(prompt: str) -> Dict[str, Any]:
    """
    Analyze stock data using Claude with retry logic.
    """
    if not ANTHROPIC_API_KEY:
        return {"error": "Anthropic API Key not set"}
        
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
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
            error_str = str(e)
            # Check for rate limit errors (429) or overloaded (529)
            if "429" in error_str or "529" in error_str or "Overloaded" in error_str:
                if attempt < max_retries - 1:
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"Claude rate limit error. Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
            
            return {"error": f"Claude Analysis Failed: {error_str}"}
            
    return {"error": "Claude Analysis Failed: Max retries exceeded"}

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
