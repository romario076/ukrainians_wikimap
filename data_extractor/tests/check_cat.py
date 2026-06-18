import asyncio
import httpx
import json

async def check_categories():
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    url = "https://uk.wikipedia.org/w/api.php"
    
    for year in [1923, 1926]:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Категорія:Народились {year}",
            "cmlimit": "max",
            "format": "json"
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            members = [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
            
            found = [m for m in members if "Ференцевич" in m]
            print(f"Year {year} category search for 'Ференцевич': {found}")

if __name__ == "__main__":
    asyncio.run(check_categories())
