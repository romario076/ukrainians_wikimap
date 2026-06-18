import asyncio
from get_wiki_data import main

if __name__ == "__main__":
    # Test for 20 years to trigger 429 logic if it's there
    asyncio.run(main(start_year=1960, end_year=1979, batch_size=20))
