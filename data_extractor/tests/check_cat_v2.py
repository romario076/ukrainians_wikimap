import asyncio
import httpx
import json

async def check_categories():
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    url = "https://uk.wikipedia.org/w/api.php"
    
    # Check both space and underscore
    for cat_title in ["Категорія:Народились 1926", "Категорія:Народились_1926"]:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cat_title,
            "cmlimit": "max",
            "format": "json"
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            members = [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
            
            # Check for Ференцевич Юрій specifically
            found = "Ференцевич Юрій" in members
            print(f"Category '{cat_title}' count: {len(members)}. Found 'Ференцевич Юрій': {found}")
            if not found:
                # Print first 5 members for debug
                print(f"  First 5: {members[:5]}")

if __name__ == "__main__":
    asyncio.run(check_categories())
