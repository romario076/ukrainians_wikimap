import asyncio
import httpx
import json

async def test_redirects():
    # 'Таня Гартфорд' redirects to 'Тетяна Гартфорд'
    # 'Річард Бінзель' should be fine
    titles = ["Таня Гартфорд", "Річард Бінзель"]
    url = "https://uk.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "exchars": 200,
        "format": "json",
        "redirects": 1
    }
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url, params=params)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            pages = data.get("query", {}).get("pages", {})
            for pid, info in pages.items():
                print(f"Page ID: {pid}, Title: {info.get('title')}")
                
            redirects = data.get("query", {}).get("redirects", [])
            print(f"Redirects: {json.dumps(redirects, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Content: {resp.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test_redirects())
