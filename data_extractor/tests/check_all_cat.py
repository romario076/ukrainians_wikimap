import asyncio
import httpx

async def check_all_cat():
    url = "https://uk.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Категорія:Народились 1926",
        "cmlimit": "500",
        "format": "json"
    }
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    all_titles = []
    
    async with httpx.AsyncClient(headers=headers) as client:
        while True:
            resp = await client.get(url, params=params)
            data = resp.json()
            members = data.get("query", {}).get("categorymembers", [])
            all_titles.extend([m["title"] for m in members])
            
            if "continue" in data:
                params.update(data["continue"])
            else:
                break
                
        found = [t for t in all_titles if "Ференцевич" in t]
        print(f"Found in category: {found}")
        print(f"Total members: {len(all_titles)}")

if __name__ == "__main__":
    asyncio.run(check_all_cat())
