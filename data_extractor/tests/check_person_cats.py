import asyncio
import httpx
import json

async def check_categories():
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    url = "https://uk.wikipedia.org/w/api.php"
    
    params = {
        "action": "query",
        "titles": "Ференцевич Юрій",
        "prop": "categories",
        "cllimit": "max",
        "format": "json"
    }
    
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for pid, info in pages.items():
            cats = [c["title"] for c in info.get("categories", [])]
            print(f"Categories for {info.get('title')}:")
            for cat in cats:
                print(f" - {cat}")

if __name__ == "__main__":
    asyncio.run(check_categories())
