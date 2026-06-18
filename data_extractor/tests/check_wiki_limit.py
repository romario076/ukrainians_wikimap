import asyncio
import httpx
import json

async def check_limit():
    # Real people from the user's list (first 30)
    titles = [
        "Руперт Вансіттарт", "Рікардо Акунья", "Рікардо Гарека", "Річард Бінзель", 
        "Сабіна Бішофф", "Салах Ассад", "Саліма Гезалі", "Сандра Велнер", 
        "Светла Бочварова", "Серж Бланко", "Серхіо Верду", "Серхіо Гойрі", 
        "Серхіо Омар Альмірон", "Скотт Гамільтон", "Софі вон Вейлер", "Стефі Баум", 
        "Стівен Голланд", "Стівен Гопкінс (режисер)", "Сьюзен Гелмс", "Сільвіо Бальдіні",
        "Таня Гартфорд", "Тереза Белланова", "Террі Бутчер", "Томас Бйоркман",
        "Томас Гернс", "Томаш Бутта", "Тім Бернгардт", "Тім Бертон", "Убальдо Акіно", "Уве Гельмес"
    ]
    
    url = "https://uk.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "exchars": 200,
        "format": "json",
    }
    headers = {"User-Agent": "UkraineHistoryScraper/6.0 (romario76@yahoo.com) Python/httpx"}
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        
        pages = data.get("query", {}).get("pages", {})
        print(f"Number of pages in response: {len(pages)}")
        
        extracts_count = sum(1 for p in pages.values() if "extract" in p)
        print(f"Number of extracts in response: {extracts_count}")
        
        # Check which titles have extracts
        found_titles = [p.get("title") for p in pages.values() if "extract" in p]
        print(f"Titles with extracts: {len(found_titles)}")
        
        if "warnings" in data:
            print(f"Warnings: {json.dumps(data['warnings'], indent=2, ensure_ascii=False)}")
        
        # If extracts_count is 20, we found the limit.
        if extracts_count == 20:
             print("\n!!! LIMIT CONFIRMED: Only 20 extracts returned even though more were requested.")

if __name__ == "__main__":
    asyncio.run(check_limit())
