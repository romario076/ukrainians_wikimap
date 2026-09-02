import asyncio
import httpx
import csv
import os
import json
import time
import pandas as pd
from typing import List, Dict, Set, Optional
from config import (
    CSV_FILE, CSV_COLUMNS, UKRAINE_ENTITIES, UKRAINE_ETHNICITIES, 
    ORIGIN_KEYWORDS, SCRAPE_LANGUAGES, UKRAINE_POLYGON, UKRAINE_ETHNIC_POLYGON, EXCHARS
)

# --- CACHING SETUP ---
CACHE_FILE = "wikidata_cache.json"

def load_cache() -> Dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache: Dict):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False) # Removed indentation for speed

# --- SPATIAL FILTERING ---
def is_point_in_polygon(lon: float, lat: float, polygon: List[tuple]) -> bool:
    """
    Ray-casting algorithm to check if a point is inside a polygon.
    """
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if lat > min(p1y, p2y):
            if lat <= max(p1y, p2y):
                if lon <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lon <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def is_in_ukraine(coords_str: Optional[str], polygon: Optional[List] = None) -> bool:
    """
    Checks if coordinates "Point(long lat)" are within a specific polygon (default: UKRAINE_POLYGON).
    """
    if not coords_str:
        return False
    if polygon is None:
        polygon = UKRAINE_POLYGON
        
    try:
        # Extract lat/lon from "Point(lon lat)"
        parts = coords_str.replace("Point(", "").replace(")", "").split()
        if len(parts) != 2:
            return False
        lon, lat = float(parts[0]), float(parts[1])
        
        return is_point_in_polygon(lon, lat, polygon)
    except:
        return False


# --- ASYNC SCRAPER CLASS ---
class WikiDataScraper:
    def __init__(self):
        self.headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
        self.cache = load_cache()
        self.resolved_dict = self.cache.get("resolved_dictionary", {})
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0, 
                                      limits=httpx.Limits(max_connections=20, max_keepalive_connections=10))
        self.wiki_sem = asyncio.Semaphore(10) # Wikipedia is more tolerant
        self.wd_sem = asyncio.Semaphore(5)    # Wikidata is very sensitive, limit to 5

    async def close(self, save=True):
        if save:
            self.cache["resolved_dictionary"] = self.resolved_dict
            save_cache(self.cache)
        await self.client.aclose()

    async def get_wiki_qids_for_year(self, year: int, lang: str) -> Dict[str, Dict]:
        """Fetch QIDs from Category:Born {year} on a specific language Wikipedia (with pagination)."""
        url = f"https://{lang}.wikipedia.org/w/api.php"
        cat_names = {
            "uk": f"Категорія:Народились {year}",
            "en": f"Category:{year} births",
            "ru": f"Категория:Родившиеся в {year} году",
            "pl": f"Kategoria:Urodzeni w {year}",
            "de": f"Kategorie:Geboren {year}",
            "fr": f"Catégorie:Naissance en {year}"
        }
        cat_title = cat_names.get(lang, f"Category:{year} births")
        
        qids = {}
        params = {
            "action": "query", "generator": "categorymembers",
            "gcmtitle": cat_title,
            "gcmlimit": "max", "prop": "pageprops",
            "ppprop": "wikibase_item", "format": "json"
        }
        
        try:
            while True:
                # Add retry logic and semaphore
                for attempt in range(4):
                    try:
                        async with self.wiki_sem:
                            resp = await self.client.get(url, params=params)
                        if resp.status_code == 200:
                            data = resp.json()
                            break
                        elif resp.status_code == 429:
                            await asyncio.sleep(5 * (attempt + 1))
                        else:
                            await asyncio.sleep(1)
                    except Exception as e:
                        if attempt == 3: raise e
                        await asyncio.sleep(2)

                pages = data.get("query", {}).get("pages", {})
                for page_id, info in pages.items():
                    qid = info.get("pageprops", {}).get("wikibase_item")
                    if qid:
                        qids[qid] = {
                            "wikipedia": f"https://{lang}.wikipedia.org/wiki/{info['title'].replace(' ', '_')}",
                            "title": info["title"]
                        }
                
                if "continue" in data:
                    params.update(data["continue"])
                else:
                    break
        except Exception as e:
            print(f"  ⚠️ Error fetching category {cat_title} ({lang}): {e}")
        return qids

    async def get_candidates_via_wikipedia(self, year: int) -> Dict[str, Dict]:
        """Fetch candidates directly from Ukrainian Wikipedia birth categories (Highly reliable, supports pagination)."""
        candidates = {}
        url = "https://uk.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": f"Категорія:Народились {year}", # Fixed: Use space as canonical separator
            "gcmtype": "page",
            "gcmlimit": "max",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "format": "json"
        }
        try:
            while True:
                data = None
                for attempt in range(4):
                    try:
                        async with self.wiki_sem:
                            resp = await self.client.get(url, params=params, timeout=30.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            break
                        elif resp.status_code == 429:
                            await asyncio.sleep(5 * (attempt + 1))
                        else:
                            await asyncio.sleep(2)
                    except Exception as e:
                        if attempt == 3: raise e
                        await asyncio.sleep(2)

                if data:
                    pages = data.get("query", {}).get("pages", {})
                    for pid, info in pages.items():
                        qid = info.get("pageprops", {}).get("wikibase_item")
                        if qid:
                            title = info.get("title", "")
                            candidates[qid] = {
                                "label": title,
                                "wiki_title": title, # Store title for extract fetching
                                "description": "Found via Wikipedia Category",
                                "birth_date": str(year),
                                "wikipedia": f"https://uk.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                "discovery_path": 7 
                            }
                    
                    if "continue" in data:
                        params.update(data["continue"])
                    else:
                        break
                else:
                    break
        except Exception as e:
            print(f"    ⚠️ Wikipedia API Error for {year}: {e}")
        return candidates

    async def fetch_wikipedia_extracts(self, titles: List[str], exchars: int = 350, batch_size: int = 50) -> Dict[str, str]:
        """Fetch the first few sentences of Wikipedia articles in batches of 50 in parallel."""
        original_titles = sorted(list(set([t for t in titles if t])))
        extracts = {}
        url = "https://uk.wikipedia.org/w/api.php"
        
        async def fetch_batch(batch, batch_index):
            batch_extracts = {}
            title_mapping = {t: t for t in batch}
            params = {
                "action": "query", "titles": "|".join(batch),
                "prop": "extracts", "exintro": True, "explaintext": True,
                "exchars": exchars, "format": "json", "redirects": 1
            }
            
            # Simple retry logic
            for attempt in range(3):
                try:
                    async with self.wiki_sem:
                        resp = await self.client.get(url, params=params, timeout=40.0)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        query_data = data.get("query", {})
                        
                        # Normalizations
                        norm_map = {n["from"]: n["to"] for n in query_data.get("normalized", [])}
                        for orig, current in title_mapping.items():
                            if current in norm_map: title_mapping[orig] = norm_map[current]
                        
                        # Redirects
                        redir_map = {r["from"]: r["to"] for r in query_data.get("redirects", [])}
                        for orig, current in title_mapping.items():
                            if current in redir_map: title_mapping[orig] = redir_map[current]
                        
                        # Extracts
                        pages = query_data.get("pages", {})
                        final_extracts = {info.get("title"): info.get("extract", "") for pid, info in pages.items() if info.get("title")}
                        
                        for orig, final in title_mapping.items():
                            batch_extracts[orig] = final_extracts.get(final, "")
                        return batch_extracts
                    elif resp.status_code == 429:
                        await asyncio.sleep(2 * (attempt + 1))
                except Exception as e:
                    if attempt == 2: print(f"    ⚠️ Wiki Extract Error batch {batch_index}: {e}")
                    await asyncio.sleep(1)
            return batch_extracts

        batches = [original_titles[i:i + batch_size] for i in range(0, len(original_titles), batch_size)]
        if batches:
            print(f"      - Fetching {len(original_titles)} extracts in {len(batches)} parallel batches...")
            results = await asyncio.gather(*[fetch_batch(b, i) for i, b in enumerate(batches)])
            for res in results:
                extracts.update(res)
                
        return extracts


    async def get_candidates_via_sparql(self, year_start: int, year_end: int) -> Dict[str, Dict]:
        """Fetch candidates from Wikidata using multiple discovery paths (Direct, Ancestry, Language, Keywords)."""
        all_results = {}
        url = "https://query.wikidata.org/sparql"
        uk_entities = " ".join([f"wd:{q}" for q in UKRAINE_ENTITIES])
        uk_ethnicities = " ".join([f"wd:{q}" for q in UKRAINE_ETHNICITIES])
        
        # Chunking years for SPARQL (Paths 1-4) to reduce number of requests
        chunk_size = 20
        for chunk_start in range(year_start, year_end + 1, chunk_size):
            chunk_end = min(chunk_start + chunk_size - 1, year_end)
            print(f"   📅 Discovery Batch: {chunk_start} - {chunk_end}")
            
            # A. Discovery via Wikipedia API (Path 7) - Parallelized
            print(f"    - Fetching Wikipedia categories for {chunk_end-chunk_start+1} years in parallel...")
            wiki_tasks = [self.get_candidates_via_wikipedia(y) for y in range(chunk_start, chunk_end + 1)]
            wiki_results = await asyncio.gather(*wiki_tasks)
            for res in wiki_results:
                all_results.update(res)
            
            # B. Discovery via SPARQL (Paths 1-4 only) - Batched for speed
            sub_queries = [
                f"""SELECT DISTINCT ?item WHERE {{
                  ?item wdt:P31 wd:Q5; wdt:P569 ?birthDate.
                  FILTER(YEAR(?birthDate) >= {chunk_start} && YEAR(?birthDate) <= {chunk_end})
                  {{
                    ?item (wdt:P27|wdt:P172|wdt:P19/wdt:P17) ?rel.
                    VALUES ?rel {{ {uk_entities} {uk_ethnicities} }}
                  }}
                }}""",
                f"""SELECT DISTINCT ?item WHERE {{
                  ?item wdt:P31 wd:Q5; wdt:P569 ?birthDate.
                  FILTER(YEAR(?birthDate) >= {chunk_start} && YEAR(?birthDate) <= {chunk_end})
                  ?item (wdt:P22|wdt:P25) ?parent.
                  ?parent (wdt:P27|wdt:P172|wdt:P19/wdt:P17) ?rel.
                  VALUES ?rel {{ {uk_entities} {uk_ethnicities} }}
                }}""",
                f"""SELECT DISTINCT ?item WHERE {{
                  ?item wdt:P31 wd:Q5; wdt:P569 ?birthDate.
                  FILTER(YEAR(?birthDate) >= {chunk_start} && YEAR(?birthDate) <= {chunk_end})
                  ?item (wdt:P103|wdt:P1412) wd:Q8798.
                }}""",
                f"""SELECT DISTINCT ?item WHERE {{
                  ?item wdt:P31 wd:Q5; wdt:P569 ?birthDate.
                  FILTER(YEAR(?birthDate) >= {chunk_start} && YEAR(?birthDate) <= {chunk_end})
                  SERVICE wikibase:box {{
                    ?item wdt:P19 ?place.
                    ?place wdt:P625 ?location.
                    bd:serviceParam wikibase:cornerSouthWest "Point(21.8 44.3)"^^geo:wktLiteral.
                    bd:serviceParam wikibase:cornerNorthEast "Point(41.1 52.8)"^^geo:wktLiteral.
                  }}
                }}"""
            ]

            for i, sq in enumerate(sub_queries):
                try:
                    # Using centralized query method with built-in retry and backoff
                    resp_text = await self._query_sparql_with_retry(sq)
                    if resp_text:
                        lines = resp_text.splitlines()
                        if len(lines) > 1:
                            for line in lines[1:]:
                                qid = line.strip().strip('"').split('/')[-1]
                                if qid and qid.startswith('Q') and qid not in all_results:
                                    all_results[qid] = {
                                        "label": "", "description": "", "birth_date": "", 
                                        "wikipedia": f"https://uk.wikipedia.org/wiki/{qid}",
                                        "discovery_path": i + 1
                                    }
                except Exception as e:
                    print(f"    ⚠️ Path {i+1} Final Failure: {e}")
                # Small pause even between successful queries to be polite
                await asyncio.sleep(1)
            
            print(f"    Total found so far: {len(all_results)}")

        return all_results

    async def _query_sparql_with_retry(self, query: str, max_retries: int = 5) -> Optional[str]:
        """Query SPARQL with exponential backoff and retry for 429/502 errors."""
        url = "https://query.wikidata.org/sparql"
        for attempt in range(max_retries):
            try:
                resp = await self.client.get(url, params={"query": query, "format": "csv"}, timeout=60.0)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 429:
                    wait_time = (2 ** attempt) + 20 # Longer wait for SPARQL
                    # print(f"    🚦 Rate limited (429). Waiting {wait_time}s before retry {attempt+1}/{max_retries}...")
                    await asyncio.sleep(wait_time)
                elif resp.status_code == 502:
                    # print(f"    ☁️ Server Busy (502). Waiting 5s before retry {attempt+1}/{max_retries}...")
                    await asyncio.sleep(5)
                else:
                    # print(f"    ⚠️ SPARQL HTTP {resp.status_code} for query.")
                    break
            except Exception as e:
                # print(f"    ❌ Network error on SPARQL attempt {attempt+1}: {e}")
                await asyncio.sleep(2)
        return None

    async def fetch_wikidata_entities(self, qid_list: List[str], props: str = "claims|labels|descriptions|sitelinks") -> Dict:
        """Fetch Wikidata entities in parallel chunks of 50."""
        if not qid_list:
            return {}
        
        url = "https://www.wikidata.org/w/api.php"
        results = {}
        
        async def fetch_chunk(chunk):
            params = {
                "action": "wbgetentities", "ids": "|".join(chunk), 
                "props": props, "languages": "uk|en", "format": "json"
            }
            for attempt in range(4):
                try:
                    async with self.wd_sem:
                        resp = await self.client.get(url, params=params)
                    
                    if resp.status_code == 200:
                        return resp.json().get("entities", {})
                    elif resp.status_code == 429:
                        wait = 10 * (attempt + 1)
                        print(f"  🚦 Wikidata rate limit (429). Waiting {wait}s...")
                        await asyncio.sleep(wait)
                except Exception as e:
                    if attempt == 3: print(f"  ⚠️ Error fetching Wikidata entities: {e}")
                    await asyncio.sleep(2)
            return {}

        chunks = [qid_list[i:i + 50] for i in range(0, len(qid_list), 50)]
        print(f"    - Fetching {len(qid_list)} entities in {len(chunks)} parallel chunks...")
        chunk_results = await asyncio.gather(*[fetch_chunk(c) for c in chunks])
        for res in chunk_results:
            results.update(res)
            
        return results

    def parse_person_claims(self, entity: Dict) -> Dict:
        claims = entity.get("claims", {})

        def get_qid_list(prop):
            return [c["mainsnak"]["datavalue"]["value"]["id"] for c in claims.get(prop, [])
                    if c.get("mainsnak", {}).get("datavalue", {}).get("type") == "wikibase-entityid"]

        def get_time_value(prop):
            c = claims.get(prop, [])
            if c and "datavalue" in c[0]["mainsnak"]:
                t = c[0]["mainsnak"]["datavalue"]["value"].get("time", "")
                return t.lstrip('+') if t else None
            return None

        # Get label and description primarily in Ukrainian, fallback to English
        labels = entity.get("labels", {})
        label = labels.get("uk", {}).get("value") or labels.get("en", {}).get("value") or ""

        descriptions = entity.get("descriptions", {})
        desc = descriptions.get("uk", {}).get("value") or descriptions.get("en", {}).get("value") or ""

        return {
            "label": label,
            "description": desc,
            "instance_of": get_qid_list("P31"),
            "birth_date": get_time_value("P569"),
            "death_date": get_time_value("P570"),
            "citizenship": get_qid_list("P27"),
            "ethnicity": get_qid_list("P172"),
            "birth_place_id": get_qid_list("P19")[0] if get_qid_list("P19") else None,
            "death_place_id": get_qid_list("P20")[0] if get_qid_list("P20") else None,
            "sex_id": get_qid_list("P21")[0] if get_qid_list("P21") else None,
            "occupations": get_qid_list("P106"),
            "fields": get_qid_list("P101"),
            "positions": get_qid_list("P39"),
            "languages": get_qid_list("P103") + get_qid_list("P1412")
        }

    async def resolve_dictionary_items(self, qids: Set[str]):
        """Resolve labels, coordinates, and countries for cities, occupations, etc."""
        to_fetch = [q for q in qids if q not in self.resolved_dict]
        if not to_fetch:
            return

        print(f" -> Resolving {len(to_fetch)} new items from Wikidata...")
        raw_data = await self.fetch_wikidata_entities(to_fetch, props="claims|labels")
        
        for qid, entity in raw_data.items():
            claims = entity.get("claims", {})
            labels = entity.get("labels", {})
            label = labels.get("uk", {}).get("value") or labels.get("en", {}).get("value") or qid
            
            coords, country = None, None
            
            # P625: Coordinate location
            p625 = claims.get("P625", [])
            if p625 and "datavalue" in p625[0]["mainsnak"]:
                val = p625[0]["mainsnak"]["datavalue"]["value"]
                coords = f"Point({val['longitude']} {val['latitude']})"
            
            # P17: Country
            p17 = claims.get("P17", [])
            if p17 and "datavalue" in p17[0]["mainsnak"]:
                country = p17[0]["mainsnak"]["datavalue"]["value"].get("id")
            
            self.resolved_dict[qid] = {"label": label, "coords": coords, "country": country}
        
        # Only save if we have many new items or on close
        if len(to_fetch) > 100:
            self.cache["resolved_dictionary"] = self.resolved_dict
            save_cache(self.cache)

# --- PIPELINE ---

async def run_async_historical_pipeline(year_start: int, year_end: int, batch_size: int = 50, scraper: Optional[WikiDataScraper] = None):
    # Use existing scraper if provided to avoid re-loading cache
    if scraper is None:
        scraper = WikiDataScraper()
        own_scraper = True
    else:
        own_scraper = False
        
    file_exists = os.path.isfile(CSV_FILE)
    
    print(f"\n🎬 Start Async Pipeline: {year_start} -> {year_end} (Broad Discovery) {CSV_FILE}")

    # Step 1: Broad Discovery via SPARQL
    candidates = await scraper.get_candidates_via_sparql(year_start, year_end)
    if not candidates:
        print(" ℹ️ No candidates found in this range.")
        return

    print(f" -> Total unique candidates found: {len(candidates)}")

    # Step 2: Fetch full details for candidates to ensure we have all properties (citizenship, ethnicity, etc.)
    candidate_qids = list(candidates.keys())
    print(f" -> Fetching full details and filtering in chunks...")
    
    chunk_size = 1000
    total_records_written = 0
    for i in range(0, len(candidate_qids), chunk_size):
        chunk_qids = candidate_qids[i:i + chunk_size]
        print(f"   🚀 [Processing Chunk {i//chunk_size + 1}: {len(chunk_qids)} items]")
        
        raw_data = await scraper.fetch_wikidata_entities(chunk_qids, props="claims|labels|descriptions|sitelinks")
        
        parsed_batch = {}
        dictionary_qids = set()
        
        for qid, entity in raw_data.items():
            if "claims" in entity:
                p_data = scraper.parse_person_claims(entity)
                # Use discovery data as base/fallback
                p_data["wikipedia"] = candidates[qid]["wikipedia"]
                if not p_data["label"]: p_data["label"] = candidates[qid]["label"]
                if not p_data["description"]: p_data["description"] = candidates[qid].get("description", "")
                p_data["discovery_path"] = candidates[qid].get("discovery_path")
                if "wiki_title" in candidates[qid]:
                    p_data["wiki_title"] = candidates[qid]["wiki_title"]
                
                parsed_batch[qid] = p_data
                
                # Dictionary items to resolve
                if p_data["birth_place_id"]: dictionary_qids.add(p_data["birth_place_id"])
                if p_data["death_place_id"]: dictionary_qids.add(p_data["death_place_id"])
                if p_data["sex_id"]: dictionary_qids.add(p_data["sex_id"])
                dictionary_qids.update(
                    p_data["instance_of"] +
                    p_data["occupations"] + p_data["fields"] + p_data["positions"] +
                    p_data["ethnicity"] + p_data["citizenship"]
                )
                # Map Wikidata sitelinks to Wikipedia titles for extraction
                ukwiki = entity.get("sitelinks", {}).get("ukwiki", {}).get("title")
                if ukwiki:
                    p_data["wiki_title"] = ukwiki

        # Step 2.5: Fetch Wikipedia Extracts for enhanced keyword matching
        wiki_titles = [p.get("wiki_title") for p in parsed_batch.values() if p.get("wiki_title")]
        print(f" -> Fetching Wikipedia extracts for {len(wiki_titles)} articles...")

        #wiki_titles = ['Ґрем Брюер']
        wiki_extracts = await scraper.fetch_wikipedia_extracts(titles=wiki_titles, exchars=EXCHARS, batch_size=20)
        for p in parsed_batch.values():
            title = p.get("wiki_title")
            p["wiki_extract"] = wiki_extracts.get(title, "")

        # scraper = WikiDataScraper()
        #[(key, parsed_batch[key])  for key in parsed_batch.keys() if parsed_batch[key]['label']=='Вейн Бабич']
        #'Q3566813'
        #'Вейн Бабич' in wiki_titles

        # Ensure all potential Ukrainian entities are resolved for diagnostic labels
        dictionary_qids.update(UKRAINE_ENTITIES)

        # Step 3: Resolve dictionary items
        await scraper.resolve_dictionary_items(dictionary_qids)

        # Step 4: Filtering and Writing
        records_written = 0
        # Open CSV once for the entire chunk's results
        with open(CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            # Write header if file is new
            if f.tell() == 0:
                writer.writeheader()
            
            for qid, p in parsed_batch.items():
                b_place = scraper.resolved_dict.get(p["birth_place_id"], {})
                d_place = scraper.resolved_dict.get(p["death_place_id"], {})

                #if 'вейн' in p['label'].lower():
                #    break

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
                wiki_text = (p.get("wiki_extract") or "").lower()
                full_text = f"{label_lower} {desc_lower} {wiki_text}"
                text_matches = [kw for kw in ORIGIN_KEYWORDS if kw.lower() in full_text]
                text_matches_val = "|".join(text_matches)

                # Check spatial against ethnic polygon if modern one fails
                born_in_ukraine_ethnic = False
                if not born_in_ukraine_spatial:
                    born_in_ukraine_ethnic = is_in_ukraine(b_place.get("coords"), polygon=UKRAINE_ETHNIC_POLYGON)

                # REFINED MATCH LOGIC:
                # 1. Born in modern Ukraine -> Always Match
                # 2. Strong markers (Citizenship, Ethnicity, Ancestry info from SPARQL, Ukrainian Language) -> Always Match
                # 3. Born in Ethnic Territories -> Match ONLY IF additional marker exists (Keywords, etc.)

                # Diagnostic: Is Ukrainian speaker?
                # Check for Q8798 in languages list
                languages = True if "Q8798" in p.get("languages", []) else False
                ancestry = p.get("discovery_path") == 2
                is_uk_wiki = p.get("discovery_path") == 7

                if born_in_ukraine_ethnic:
                    born_in_ukraine_ethnic_ext = born_in_ukraine_ethnic and (is_citizen_val or is_ethnic_val or text_matches_val or languages or ancestry)
                else:
                    born_in_ukraine_ethnic_ext = False

                person_match = (born_in_ukraine_spatial or born_in_ukraine_ethnic_ext or born_in_ukraine_entity or is_citizen_val
                                    or is_ethnic_val or text_matches_val or languages or ancestry)
                                    
                # Discovery paths 2 (Ancestry), 3 (Language) and 5 (Keywords) are already strong indicators
                #is_from_discovery = p.get("discovery_path") in [2, 3, 5]

                #is_match = False
                #if born_in_ukraine_spatial:
                #    is_match = True
                #elif is_from_discovery:
                #    is_match = True
                #elif born_in_ukraine_ethnic and has_extra_marker:
                #    is_match = True
                #elif has_extra_marker and not born_in_ukraine_ethnic:
                #    # This covers emigrants (e.g. born in USA but citizenship=Ukraine or keywords=Ukrainian origin)
                #    is_match = True

                if person_match:
                    type_labels = [scraper.resolved_dict.get(t, {}).get("label", t) for t in p["instance_of"]]
                    row = {
                        "PersonName": p["label"] or qid,
                        "InstanceOf": ", ".join(type_labels),
                        "InstanceOfIDs": ", ".join(p["instance_of"]),
                        "BirthPlace": b_place.get("label", ""),
                        "BirthDate": p["birth_date"],
                        "Coordinates": b_place.get("coords", ""),
                        "DeathPlace": d_place.get("label", ""),
                        "Coordinates_death": d_place.get("coords", ""),
                        "DeathDate": p["death_date"],
                        "WikipediaURL": p["wikipedia"],
                        "Sex": scraper.resolved_dict.get(p["sex_id"], {}).get("label", ""),
                        "Description": p["description"],
                        "WikiText": full_text,
                        "Occupation": ", ".join([scraper.resolved_dict.get(o, {}).get("label", o) for o in p["occupations"]]),
                        "Field": ", ".join([scraper.resolved_dict.get(f, {}).get("label", f) for f in p["fields"]]),
                        "Position": ", ".join([scraper.resolved_dict.get(pos, {}).get("label", pos) for pos in p["positions"]]),
                        "Ethnicity": ", ".join([scraper.resolved_dict.get(eth, {}).get("label", eth) for eth in p["ethnicity"]]),
                        "IsCitizen": is_citizen_val,
                        "IsEthnic": is_ethnic_val,
                        "BornEntity": scraper.resolved_dict.get(b_place.get("country"), {}).get("label", b_place.get("country")) if born_in_ukraine_entity else "",
                        "BornSpatial": "Yes" if born_in_ukraine_spatial else ("Ethnic" if born_in_ukraine_ethnic else "No"),
                        "IsTextMatch": text_matches_val,
                        "IsSpeaker": "Yes" if languages else "Unknown",
                        "IsAncestry": "Yes" if ancestry else "Unknown"
                    }

                    if not row["Ethnicity"] and (text_matches_val):
                        row["Ethnicity"] = "Detected by metadata"
                        
                    writer.writerow(row)
                    records_written += 1

        total_records_written = total_records_written + records_written
        print(f"💾 Chunk processed! Records written: {records_written}; Total Records written: {total_records_written}")
        await asyncio.sleep(1)

    if own_scraper:
        await scraper.close()
    
    print(f"🎉 DONE! Results in '{CSV_FILE}'.")
    return None # Return None instead of loading the whole CSV into RAM
