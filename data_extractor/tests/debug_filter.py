import asyncio
import httpx
from tools import WikiDataScraper, is_in_ukraine
from config import UKRAINE_ENTITIES, UKRAINE_ETHNIC_POLYGON, UKRAINE_POLYGON, UKRAINE_ETHNICITIES, ORIGIN_KEYWORDS

async def debug_ferencevych():
    scraper = WikiDataScraper()
    qid = "Q16721495" # Юрій Ференцевич
    
    # 1. Fetch raw data
    raw_data = await scraper.fetch_wikidata_entities([qid], props="claims|labels|descriptions|sitelinks")
    entity = raw_data.get(qid, {})
    
    if not entity:
        print("Entity not found in Wikidata fetch.")
        return

    # 2. Parse claims
    p = scraper.parse_person_claims(entity)
    p["wikipedia"] = f"https://uk.wikipedia.org/wiki/Ференцевич_Юрій"
    p["discovery_path"] = 1 # Assume found via SPARQL Path 1
    
    ukwiki = entity.get("sitelinks", {}).get("ukwiki", {}).get("title")
    if ukwiki:
        p["wiki_title"] = ukwiki

    # 3. Resolve dictionary items
    dictionary_qids = {p["birth_place_id"], p["death_place_id"], p["sex_id"]}
    dictionary_qids.update(p["occupations"] + p["fields"] + p["positions"] + p["ethnicity"] + p["citizenship"])
    dictionary_qids.discard(None)
    
    await scraper.resolve_dictionary_items(dictionary_qids)
    
    # 4. Filter logic (copy-pasted from tools.py)
    b_place = scraper.resolved_dict.get(p["birth_place_id"], {})
    d_place = scraper.resolved_dict.get(p["death_place_id"], {})

    # Check citizenship criteria
    citizen_matches = [cid for cid in p["citizenship"] if cid in UKRAINE_ENTITIES]
    is_citizen_val = ", ".join([scraper.resolved_dict.get(c, {}).get('label', c) for c in citizen_matches])
    if b_place.get("country") and not citizen_matches:
        citizen_matches = [cid for cid in [b_place.get("country")] if cid in UKRAINE_ENTITIES]
        is_citizen_val = ", ".join([scraper.resolved_dict.get(c, {}).get('label', c) for c in citizen_matches])
    
    # Check ethnicity criteria
    ethnic_matches = [eth for eth in p["ethnicity"] if eth in UKRAINE_ETHNICITIES]
    is_ethnic_val = ", ".join([scraper.resolved_dict.get(e, {}).get('label', e) for e in ethnic_matches])

    # Check birth location criteria
    born_in_ukraine_entity = b_place.get("country") in UKRAINE_ENTITIES
    born_in_ukraine_spatial = is_in_ukraine(coords_str=b_place.get("coords"), polygon=UKRAINE_POLYGON)
    
    desc_lower = (p["description"] or "").lower()
    label_lower = (p["label"] or "").lower()
    
    # Simulate extraction - we can't fetch it easily here but let's try
    wiki_text = ""
    full_text = f"{label_lower} {desc_lower} {wiki_text}"
    text_matches = [kw for kw in ORIGIN_KEYWORDS if kw.lower() in full_text]
    text_matches_val = "|".join(text_matches)

    born_in_ukraine_ethnic = False
    if not born_in_ukraine_spatial:
        born_in_ukraine_ethnic = is_in_ukraine(b_place.get("coords"), polygon=UKRAINE_ETHNIC_POLYGON)

    languages = True if "Q8798" in p.get("languages", []) else False
    ancestry = p.get("discovery_path") == 2

    if born_in_ukraine_ethnic:
        born_in_ukraine_ethnic_ext = born_in_ukraine_ethnic and (is_citizen_val or is_ethnic_val or text_matches_val or languages or ancestry)
    else:
        born_in_ukraine_ethnic_ext = False

    person_match = (born_in_ukraine_spatial or born_in_ukraine_ethnic_ext or born_in_ukraine_entity or is_citizen_val
                        or is_ethnic_val or text_matches_val or languages or ancestry)

    print(f"--- DEBUG RESULTS for {p['label']} ---")
    print(f"born_in_ukraine_spatial: {born_in_ukraine_spatial}")
    print(f"born_in_ukraine_entity: {born_in_ukraine_entity} (Country: {b_place.get('country')})")
    print(f"is_citizen_val: '{is_citizen_val}'")
    print(f"is_ethnic_val: '{is_ethnic_val}'")
    print(f"born_in_ukraine_ethnic_ext: {born_in_ukraine_ethnic_ext}")
    print(f"text_matches_val: '{text_matches_val}'")
    print(f"languages: {languages}")
    print(f"ancestry: {ancestry}")
    print(f"FINAL person_match: {person_match}")

    await scraper.close()

if __name__ == "__main__":
    asyncio.run(debug_ferencevych())
