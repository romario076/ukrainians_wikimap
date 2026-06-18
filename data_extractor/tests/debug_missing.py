import asyncio
import httpx
import json

import sys

# Fix encoding for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

async def check_individuals():
    # Rick Danko (Q539944), Paul Poberezny (Q1565277), Bill Barilko (Q716546)
    qids = ["Q539944", "Q1565277", "Q716546"]



    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "ids": "|".join(qids),
        "props": "claims|labels|descriptions|sitelinks",
        "languages": "uk|en",
        "format": "json"
    }
    
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code}")
            print(resp.text)
            return
        
        try:
            data = resp.json().get("entities", {})
        except Exception as e:
            print(f"JSON Error: {e}")
            print(resp.text)
            return

        
        for qid, entity in data.items():
            print(f"\n--- {qid} ({entity.get('labels', {}).get('uk', {}).get('value') or entity.get('labels', {}).get('en', {}).get('value')}) ---")
            claims = entity.get("claims", {})
            
            # P172: Ethnicity
            ethnicity = [c["mainsnak"]["datavalue"]["value"]["id"] for c in claims.get("P172", [])]
            print(f"P172 (Ethnicity): {ethnicity}")
            
            # P27: Citizenship
            citizenship = [c["mainsnak"]["datavalue"]["value"]["id"] for c in claims.get("P27", [])]
            print(f"P27 (Citizenship): {citizenship}")
            
            # P19: Birth Place
            birth_place = [c["mainsnak"]["datavalue"]["value"]["id"] for c in claims.get("P19", [])]
            print(f"P19 (Birth Place): {birth_place}")
            
            # Parents
            parents = [c["mainsnak"]["datavalue"]["value"]["id"] for c in (claims.get("P22", []) + claims.get("P25", []))]
            print(f"Parents (P22, P25): {parents}")

            # Description (UK)
            desc_uk = entity.get("descriptions", {}).get("uk", {}).get("value")
            print(f"Description (UK): {desc_uk}")

            # sitelinks (UK)
            ukwiki = entity.get("sitelinks", {}).get("ukwiki", {}).get("title")
            print(f"UK Wiki Title: {ukwiki}")

            if ukwiki:
                # Fetch extract
                wiki_url = "https://uk.wikipedia.org/w/api.php"
                wiki_params = {
                    "action": "query", "titles": ukwiki,
                    "prop": "extracts", "exintro": False, "explaintext": True,
                    "exchars": 1500, "format": "json", "redirects": 1
                }
                wiki_resp = await client.get(wiki_url, params=wiki_params)
                wiki_data = wiki_resp.json()
                pages = wiki_data.get("query", {}).get("pages", {})
                for pid, info in pages.items():
                    extract = info.get("extract", "")
                    print(f"Wiki Extract (truncated to 500): {extract[:500]}...")
                    
                    keywords = ["українськ", "походження", "емігрант", "батьки"]
                    found = [kw for kw in keywords if kw.lower() in extract.lower()]
                    print(f"Found keywords in full extract: {found}")


if __name__ == "__main__":
    asyncio.run(check_individuals())
