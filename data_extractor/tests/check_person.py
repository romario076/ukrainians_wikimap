import asyncio
import httpx
import json

async def check_person():
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    
    # 1. Search for Yuriy Ferencevych
    search_url = "https://www.wikidata.org/w/api.php"
    search_params = {
        "action": "wbsearchentities",
        "search": "Ференцевич Юрій",
        "language": "uk",
        "format": "json"
    }
    
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(search_url, params=search_params)
        search_data = resp.json()
        
        if not search_data.get("search"):
            print("Person not found in Wikidata search.")
            return
            
        qid = search_data["search"][0]["id"]
        print(f"Found QID: {qid} for Ференцевич Юрій")
        
        # 2. Get entity details
        entity_url = "https://www.wikidata.org/w/api.php"
        entity_params = {
            "action": "wbgetentities",
            "ids": qid,
            "props": "claims|labels|descriptions|sitelinks",
            "format": "json"
        }
        
        resp = await client.get(entity_url, params=entity_params)
        entity_data = resp.json()
        entity = entity_data.get("entities", {}).get(qid, {})
        
        # 3. Check specific claims
        claims = entity.get("claims", {})
        
        p569 = claims.get("P569", []) # Birth date
        birth_date = p569[0]["mainsnak"]["datavalue"]["value"]["time"] if p569 else "N/A"
        
        p19 = claims.get("P19", []) # Birth place
        birth_place_qid = p19[0]["mainsnak"]["datavalue"]["value"]["id"] if p19 else "N/A"
        
        p27 = claims.get("P27", []) # Citizenship
        citizenship_qids = [c["mainsnak"]["datavalue"]["value"]["id"] for c in p27]
        
        p172 = claims.get("P172", []) # Ethnicity
        ethnicity_qids = [e["mainsnak"]["datavalue"]["value"]["id"] for e in p172]
        
        uk_wiki = entity.get("sitelinks", {}).get("ukwiki", {}).get("title", "N/A")
        
        print(f"Birth Date: {birth_date}")
        print(f"Birth Place QID: {birth_place_qid}")
        print(f"Citizenships: {citizenship_qids}")
        print(f"Ethnicities: {ethnicity_qids}")
        print(f"UK Wikipedia Title: {uk_wiki}")

        # 4. Check if Lviv (Q36036) is in UKRAINE_ENTITIES or if its coordinates are in polygon
        if birth_place_qid != "N/A":
            resp = await client.get(entity_url, params={"action": "wbgetentities", "ids": birth_place_qid, "props": "claims|labels", "format": "json"})
            bp_data = resp.json().get("entities", {}).get(birth_place_qid, {})
            bp_claims = bp_data.get("claims", {})
            
            p625 = bp_claims.get("P625", []) # Coordinates
            coords = p625[0]["mainsnak"]["datavalue"]["value"] if p625 else "N/A"
            print(f"Birth Place Coordinates: {coords}")
            
            p17 = bp_claims.get("P17", []) # Country
            country_qid = p17[0]["mainsnak"]["datavalue"]["value"]["id"] if p17 else "N/A"
            print(f"Birth Place Country QID: {country_qid}")

if __name__ == "__main__":
    asyncio.run(check_person())
