import httpx
import asyncio
import traceback

async def test_sparql():
    url = "https://query.wikidata.org/sparql"
    
    query = """
    SELECT ?item ?itemLabel ?desc WHERE {
      ?item wdt:P31 wd:Q5.
      ?item wdt:P569 ?birthDate.
      FILTER(YEAR(?birthDate) >= 800 && YEAR(?birthDate) <= 850)
      SERVICE wikibase:label { 
        bd:serviceParam wikibase:language "en,uk". 
        ?item schema:description ?desc.
      }
      FILTER(CONTAINS(LCASE(?desc), "kiev") || CONTAINS(LCASE(?desc), "київ") || CONTAINS(LCASE(?desc), "rus"))
    } 
    """
    
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    async with httpx.AsyncClient(headers=headers) as client:
        try:
            resp = await client.get(url, params={"query": query, "format": "json"}, timeout=30.0)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", {}).get("bindings", [])
                print(f"Found {len(results)} results")
                for r in results:
                    print(r["item"]["value"], r["itemLabel"]["value"], r.get("desc", {}).get("value", ""))
            else:
                print(f"Error status: {resp.status_code}")
                print(resp.text[:500])
        except Exception as e:
            traceback.print_exc()

asyncio.run(test_sparql())
