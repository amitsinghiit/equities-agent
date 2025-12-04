import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional

def scrape_screener_data(symbol: str) -> Dict[str, Any]:
    """
    Scrapes financial data from screener.in for a given stock symbol.
    Returns comprehensive financial metrics including growth rates, returns, etc.
    """
    
    # Remove .NS or .BO suffix if present
    clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
    
    # Function to fetch and parse data from a specific URL
    def fetch_data(url_suffix):
        url = f"https://www.screener.in/company/{clean_symbol}{url_suffix}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            result = {
                'compounded_sales_growth': {},
                'compounded_profit_growth': {},
                'stock_price_cagr': {},
                'return_on_equity': {},
                'shareholding_pattern': {},
                'top_ratios': {}
            }
            
            # Find all tables
            tables = soup.find_all('table')
            
            data_found = False
            
            # 1. Parse Growth Tables
            for table in tables:
                table_headers = table.find_all('th')
                if not table_headers:
                    continue
                    
                header_text = table_headers[0].get_text(strip=True)
                
                target_dict = None
                if 'Compounded Sales Growth' in header_text:
                    target_dict = result['compounded_sales_growth']
                elif 'Compounded Profit Growth' in header_text:
                    target_dict = result['compounded_profit_growth']
                elif 'Stock Price CAGR' in header_text:
                    target_dict = result['stock_price_cagr']
                elif 'Return on Equity' in header_text:
                    target_dict = result['return_on_equity']
                
                if target_dict is not None:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) == 2:
                            period = cells[0].get_text(strip=True).replace(':', '')
                            value = cells[1].get_text(strip=True)
                            
                            # Clean up value
                            if value == '%':
                                value = 'N/A'
                            
                            if period and value:
                                target_dict[period] = value
                                if value != 'N/A':
                                    data_found = True

            # 2. Parse Shareholding Pattern (Quarterly)
            shp_section = soup.find('div', id='quarterly-shp')
            if shp_section:
                shp_table = shp_section.find('table', class_='data-table')
                if shp_table:
                    # Get Quarters (Headers)
                    header_row = shp_table.find('thead').find('tr')
                    quarters = [th.get_text(strip=True) for th in header_row.find_all('th')[1:]] # Skip first empty th
                    
                    result['shareholding_pattern'] = {
                        'quarters': quarters,
                        'data': {}
                    }
                    
                    # Get Rows
                    rows = shp_table.find('tbody').find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if not cells:
                            continue
                            
                        category = cells[0].get_text(strip=True).replace('+', '').strip()
                        values = [c.get_text(strip=True) for c in cells[1:]]
                        
                        if category and values:
                            result['shareholding_pattern']['data'][category] = values
                            data_found = True
            
            # 3. Parse Balance Sheet for Debt to Equity (if missing in Top Ratios)
            # We do this before Top Ratios so we can populate it if missing
            bs_section = soup.find('section', id='balance-sheet')
            if bs_section:
                bs_table = bs_section.find('table', class_='data-table')
                if bs_table:
                    # We need the last column (most recent data)
                    # Rows to find: "Borrowings", "Share Capital", "Reserves"
                    
                    borrowings = 0.0
                    equity = 0.0
                    
                    rows = bs_table.find('tbody').find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if not cells: continue
                        
                        row_name = cells[0].get_text(strip=True).replace('+', '').strip()
                        # Get the last value (most recent)
                        last_val_str = cells[-1].get_text(strip=True).replace(',', '')
                        
                        try:
                            val = float(last_val_str)
                        except ValueError:
                            val = 0.0
                            
                        if row_name == 'Borrowings':
                            borrowings = val
                        elif row_name == 'Share Capital':
                            equity += val
                        elif row_name == 'Reserves':
                            equity += val
                    
                    if equity > 0:
                        d_e = borrowings / equity
                        # Initialize top_ratios if not exists (though we initialized result['top_ratios'] earlier)
                        if 'top_ratios' not in result:
                            result['top_ratios'] = {}
                        result['top_ratios']['Debt to equity'] = f"{d_e:.2f}"

            # 4. Parse Top Ratios (Market Cap, PE, etc.)
            top_ratios = result.get('top_ratios', {})
            ratios_ul = soup.find('ul', id='top-ratios')
            if ratios_ul:
                for li in ratios_ul.find_all('li'):
                    name_span = li.find('span', class_='name')
                    value_span = li.find('span', class_='value')
                    
                    if name_span and value_span:
                        name = name_span.get_text(strip=True)
                        # Get text but preserve spaces if needed, mostly just want the number and unit
                        # The value span might contain a span class="number"
                        value = value_span.get_text(" ", strip=True)
                        top_ratios[name] = value
                        data_found = True
            
            result['top_ratios'] = top_ratios
            
            return result, data_found
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None, False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 1. Try Consolidated first
    data, valid = fetch_data("/consolidated/")
    source = "Consolidated"
    
    # 2. If Consolidated failed or has no valid data (all N/A), try Standalone
    if not data or not valid:
        # print("Consolidated data missing or empty, trying Standalone...")
        standalone_data, standalone_valid = fetch_data("/")
        if standalone_data and standalone_valid:
            data = standalone_data
            source = "Standalone"
            
    if not data:
         return {
            'compounded_sales_growth': {},
            'compounded_profit_growth': {},
            'stock_price_cagr': {},
            'return_on_equity': {},
            'shareholding_pattern': {},
            'top_ratios': {},
            'source': 'N/A'
        }
    
    data['source'] = source
    return data

def extract_growth_metrics(section) -> Dict[str, str]:
    """Extract growth metrics from a section element"""
    metrics = {}
    
    # Find all nested items
    items = section.find_all('span')
    
    for i in range(0, len(items)-1, 2):
        period = items[i].get_text(strip=True)
        value = items[i+1].get_text(strip=True)
        
        if period and value:
            metrics[period] = value
    
    return metrics

def extract_period(text: str) -> Optional[str]:
    """Extract time period from text (e.g., '10 Years', '5 Years', etc.)"""
    patterns = [
        r'10\s*Years?',
        r'5\s*Years?',
        r'3\s*Years?',
        r'1\s*Year',
        r'TTM',
        r'Last\s*Year'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None

def parse_percentage(value: str) -> str:
    """Parse percentage value, handling various formats"""
    # Remove % sign and extra spaces
    cleaned = value.strip().replace('%', '').strip()
    
    # Handle special cases
    if cleaned in ['-', 'N/A', '']:
        return 'N/A'
    
    return f"{cleaned}%"
