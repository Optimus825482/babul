import requests
from bs4 import BeautifulSoup
import re
import json
import sys

url = 'https://www.arabam.com/ikinci-el?searchText=BMW+320i&yearMin=2020&yearMax=2020&sort=price'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9',
}

print("Fetching...")
sys.stdout.flush()

r = requests.get(url, headers=headers, timeout=15)
print(f"Status: {r.status_code}")
sys.stdout.flush()

soup = BeautifulSoup(r.text, 'lxml')
rows = soup.select('tr.listing-list-item')
print(f"Total listings: {len(rows)}")
sys.stdout.flush()

for i, row in enumerate(rows[:5]):
    print(f"\n{'='*60}")
    print(f"ILAN #{i+1}")
    print(f"{'='*60}")
    
    # ID
    imp_id = row.get('data-imp-id', '')
    print(f"ID: {imp_id}")
    
    # Link
    link = row.select_one('a[href*="/ilan/"]')
    if link:
        print(f"Link: {link.get('href', '')}")
    
    # Image
    img = row.select_one('img')
    if img:
        print(f"Img src: {img.get('src', '')[:100]}")
        print(f"Img data-src: {img.get('data-src', '')[:100]}")
        print(f"Img alt: {img.get('alt', '')[:80]}")
    
    # Model name
    model_div = row.select_one('div.listing-text-new.word-break.val-middle')
    if not model_div:
        model_div = row.select_one('div.listing-modelname')
    if not model_div:
        # Try finding any div with model-like class
        for d in row.select('div'):
            cls = d.get('class', [])
            if any('model' in str(c) for c in cls):
                model_div = d
                break
    if model_div:
        print(f"Model: {model_div.get_text(strip=True)[:80]}")
    
    # Title
    title_div = row.select_one('div.listing-text-new.listing-title-lines')
    if not title_div:
        title_div = row.select_one('div.listing-title-lines')
    if title_div:
        print(f"Title: {title_div.get_text(strip=True)[:100]}")
    
    # Price
    price = row.select_one('span.listing-price')
    if not price:
        # Try class containing price
        for el in row.select('[class*="price"]'):
            if el.get_text(strip=True):
                price = el
                break
    if price:
        print(f"Price: {price.get_text(strip=True)}")
    
    # Location
    loc_spans = row.select('span[title]')
    locations = [(s.get('title',''), s.get_text(strip=True)) for s in loc_spans if s.get_text(strip=True)]
    if locations:
        print(f"Locations: {locations}")
    
    # All text cells (td)
    tds = row.select('td')
    for j, td in enumerate(tds):
        txt = td.get_text(strip=True)
        if txt and len(txt) < 100:
            print(f"  TD[{j}]: {txt[:80]}")
    
    # Year
    year_match = re.search(r'\b(20\d{2})\b', row.get_text())
    if year_match:
        print(f"Year found: {year_match.group(1)}")
    
    # Date
    date_pattern = r'\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}'
    date_match = re.search(date_pattern, row.get_text())
    if date_match:
        print(f"Date: {date_match.group(0)}")

    # Print raw HTML of first row for analysis
    if i == 0:
        print(f"\n--- RAW HTML (first row) ---")
        html_str = str(row)
        print(html_str[:3000])

sys.stdout.flush()
