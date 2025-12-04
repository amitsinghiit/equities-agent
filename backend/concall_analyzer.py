import requests
from bs4 import BeautifulSoup
import os
import tempfile
from typing import Dict, Optional
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def scrape_latest_concall_ppt(symbol: str) -> Optional[str]:
    """
    Scrape the most recent concall PPT link from Screener.in
    
    Args:
        symbol: Stock symbol (e.g., 'BALKRISIND')
    
    Returns:
        URL of the most recent PPT, or None if not found
    """
    clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
    url = f"https://www.screener.in/company/{clean_symbol}/consolidated/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the Concalls section
        concalls_section = soup.find('h3', string='Concalls')
        if not concalls_section:
            return None
        
        # Find the parent container
        concalls_container = concalls_section.find_parent('div').find_next_sibling('div')
        if not concalls_container:
            return None
        
        # Find all list items (each represents a concall period)
        list_items = concalls_container.find_all('li', class_='flex')
        
        if not list_items:
            return None
        
        # Get the first (most recent) item
        first_item = list_items[0]
        
        # Find the PPT link
        ppt_link = first_item.find('a', string='PPT')
        if ppt_link and ppt_link.get('href'):
            return ppt_link['href']
        
        return None
        
    except Exception as e:
        print(f"Error scraping concall PPT: {e}")
        return None

def download_ppt(url: str) -> Optional[str]:
    """
    Download PPT/PDF file to a temporary location
    
    Args:
        url: URL of the PPT/PDF file
    
    Returns:
        Path to the downloaded file, or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            return None
        
        # Create a temporary file
        suffix = '.pdf' if 'pdf' in url.lower() else '.pptx'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(response.content)
        temp_file.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error downloading PPT: {e}")
        return None

def analyze_concall_with_gemini(file_path: str, symbol: str) -> Dict[str, str]:
    """
    Analyze the concall presentation using Gemini API
    
    Args:
        file_path: Path to the downloaded PPT/PDF file
        symbol: Stock symbol for context
    
    Returns:
        Dictionary with analysis results
    """
    if not GEMINI_API_KEY:
        return {
            "error": "Gemini API key not configured",
            "summary": "Unable to analyze concall presentation. Please configure GEMINI_API_KEY environment variable."
        }
    
    try:
        # Upload the file to Gemini
        uploaded_file = genai.upload_file(file_path)
        
        # Create the model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create a comprehensive prompt
        prompt = f"""
You are analyzing an investor presentation/concall document for {symbol}. 

Please provide a comprehensive analysis covering the following aspects in 30-40 sentences:

1. **Future Guidance & Outlook** (8-10 sentences):
   - Revenue and profit projections
   - Growth targets and timelines
   - Expansion plans and capex
   - Market opportunities being targeted
   - Strategic initiatives planned

2. **Key Achievements & Highlights** (8-10 sentences):
   - Recent financial performance
   - Operational milestones achieved
   - Market share gains or competitive advantages
   - Product launches or innovations
   - Awards, certifications, or recognitions

3. **Risks & Challenges** (8-10 sentences):
   - Market risks and competitive threats
   - Regulatory or compliance challenges
   - Supply chain or operational risks
   - Financial risks (debt, forex, etc.)
   - Industry-specific headwinds

4. **Strategic Focus Areas** (6-8 sentences):
   - Key priorities for the coming quarters
   - Investment areas (R&D, technology, infrastructure)
   - Sustainability and ESG initiatives
   - Geographic or segment focus

Please write in a clear, professional tone suitable for investors. Focus on concrete numbers, timelines, and specific initiatives mentioned in the presentation.
"""
        
        # Generate the analysis
        response = model.generate_content([uploaded_file, prompt])
        
        # Clean up the uploaded file
        try:
            os.unlink(file_path)
        except:
            pass
        
        return {
            "summary": response.text,
            "source": "Gemini AI Analysis",
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error analyzing with Gemini: {e}")
        return {
            "error": str(e),
            "summary": f"Failed to analyze concall presentation: {str(e)}",
            "status": "error"
        }

def get_concall_analysis(symbol: str) -> Dict[str, str]:
    """
    Main function to get concall analysis for a stock
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Dictionary with analysis or error message
    """
    # Step 1: Scrape the PPT link
    ppt_url = scrape_latest_concall_ppt(symbol)
    if not ppt_url:
        return {
            "error": "No concall presentation found",
            "summary": "No recent concall presentation available for this company on Screener.in",
            "status": "not_found"
        }
    
    # Step 2: Download the PPT
    file_path = download_ppt(ppt_url)
    if not file_path:
        return {
            "error": "Failed to download presentation",
            "summary": "Could not download the concall presentation file",
            "status": "download_failed"
        }
    
    # Step 3: Analyze with Gemini
    analysis = analyze_concall_with_gemini(file_path, symbol)
    
    return analysis
