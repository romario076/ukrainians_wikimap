import asyncio
import httpx
from config import UKRAINE_ENTITIES, UKRAINE_ETHNICITIES

async def test_sparql():
    uk_entities = " ".join([f"wd:{q}" for q in UKRAINE_ENTITIES])
    uk_ethnicities = " ".join([f"wd:{q}" for q in UKRAINE_ETHNICITIES])
    
    query = f"""SELECT DISTINCT ?item ?itemLabel WHERE {{
      ?item wdt:P31 wd:Q5; wdt:P569 ?birthDate.
      FILTER(YEAR(?birthDate) = 1926)
      {{
        ?item (wdt:P27|wdt:P172|wdt:P19/wdt:P17) ?rel.
        VALUES ?rel {{ {uk_entities} {uk_ethnicities} }}
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "uk,en". }}
    }}"""
    
    url = "https://query.wikidata.org/sparql"
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url, params={"query": query, "format": "json"}, timeout=60.0)
        if resp.status_code == 200:
            data = resp.json()
            bindings = data.get("results", {}).get("bindings", [])
            found = [b["itemLabel"]["value"] for b in bindings if "Ференцевич" in b["itemLabel"]["value"]]
            print(f"Found in SPARQL: {found}")
            print(f"Total results: {len(bindings)}")
        else:
            print(f"SPARQL Error: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_sparql())
