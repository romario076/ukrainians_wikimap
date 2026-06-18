import asyncio
import json
from tools import WikiDataScraper

async def test_person():
    scraper = WikiDataScraper()
    # Dobronega Volodymyrivna
    qid = "Q263296" 
    
    print(f"Fetching details for {qid}...")
    entities = await scraper.fetch_wikidata_entities([qid])
    
    if qid not in entities:
        print("Failed to fetch entity")
        return
        
    entity = entities[qid]
    
    # Simulate parsing
    claims = entity.get("claims", {})
    loc_ids = set()
    for prop in ["P19", "P20", "P119"]:
        for c in claims.get(prop, []):
            try:
                loc_ids.add(c["mainsnak"]["datavalue"]["value"]["id"])
            except: pass
            
    print(f"Location IDs found: {loc_ids}")
    
    # Resolve locations (updates internal dict)
    await scraper.resolve_dictionary_items(list(loc_ids))
    
    # Parse person
    person_data = scraper.parse_person_claims(entity)
    
    print("\nParsed Data:")
    print(json.dumps(person_data, indent=2, ensure_ascii=False))
    
    await scraper.close(save=False)

if __name__ == "__main__":
    asyncio.run(test_person())
