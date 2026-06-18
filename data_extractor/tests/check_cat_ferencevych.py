import asyncio
import httpx

async def check_cat():
    url = "https://uk.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Категорія:Народились 1926",
        "cmlimit": "max",
        "format": "json"
    }
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        members = data.get("query", {}).get("categorymembers", [])
        titles = [m["title"] for m in members]
        
        found = [t for t in titles if "Ференцевич" in t]
        print(f"Found in category: {found}")
        print(f"Total members: {len(titles)}")

if __name__ == "__main__":
    asyncio.run(check_cat())
