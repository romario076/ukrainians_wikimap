import asyncio
from tools import WikiDataScraper
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def verify():
    scraper = WikiDataScraper()
    year = 1926
    print(f"Checking candidates for year {year}...")
    candidates = await scraper.get_candidates_via_wikipedia(year)
    
    print(f"Total candidates found: {len(candidates)}")
    
    qid = "Q16721495" # Юрій Ференцевич
    if qid in candidates:
        print(f"SUCCESS: Yuriy Ferencevych ({qid}) found in candidates!")
        print(f"Details: {candidates[qid]}")
    else:
        print(f"FAILURE: Yuriy Ferencevych ({qid}) NOT found in candidates.")
        
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(verify())
