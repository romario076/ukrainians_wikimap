import asyncio
import httpx
import json
import sys
import os

# Import the class from tools.py
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from tools import WikiDataScraper

async def verify():
    scraper = WikiDataScraper()
    # 'Таня Гартфорд' redirects to 'Таня Хартфорд'
    # 'Тереза Белланова' redirects to 'Тереза Белланова' (normalized/same)
    titles = ["Таня Гартфорд", "Тереза Белланова", "Річард Бінзель"]
    
    print(f"Testing titles: {titles}")
    extracts = await scraper.fetch_wikipedia_extracts(titles, exchars=200)
    
    for title in titles:
        extract = extracts.get(title, "")
        if extract:
            # We skip printing the actual extract to avoid encoding issues in terminal if it contains unusual chars
            print(f"FOUND extract for '{title}' (length: {len(extract)})")
        else:
            print(f"MISSING extract for '{title}'")
            
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(verify())
