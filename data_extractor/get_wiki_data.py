import asyncio
import os
import json
import warnings
import sys
import time
from tools import run_async_historical_pipeline
from pathlib import Path
from datetime import datetime
from config import CHECKPOINT_FILE, CSV_FILE

# Встановлюємо UTF-8 для виводу в консоль Windows, щоб уникнути помилок з емодзі
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

warnings.filterwarnings(action='ignore')



def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"last_year": None}

def save_checkpoint(year):
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({"last_year": year}, f)

async def main(start_year, end_year, batch_size=5):
    from tools import WikiDataScraper

    checkpoint = load_checkpoint()
    if checkpoint["last_year"]:
        start_year = checkpoint["last_year"] + 1
        print(f"🔄 Резюмуємо з року {start_year}")

    if start_year > end_year:
        print("✅ Всі роки з вказаного діапазону вже оброблені.")
        return

    scraper = WikiDataScraper()
    try:
        # Обробляємо невеликими пачками, щоб кожна пачка була зафіксована в чекпойнті
        for year in range(start_year, end_year + 1, batch_size):
            st = datetime.now()
            current_batch_end = min(year + batch_size - 1, end_year)
            await run_async_historical_pipeline(year, current_batch_end, batch_size=batch_size, scraper=scraper)
            save_checkpoint(current_batch_end)
            print(f"📍 Чекпойнт: роки до {current_batch_end} включно збережено. Час:", str(datetime.now()-st))

    except Exception as e:
        print(f"❌ Критична помилка в пайплайні: {e}")
    finally:
        await scraper.close()
        print("\n🏁 Робота завершена.")



# --- НАЛАШТУВАННЯ ДІАПАЗОНУ ---
start_year = 700
end_year = 860
batch_size = 20
remove_cache = True  # Змініть на True, якщо хочете почати з нуля (це видалить CSV!)


if remove_cache:
    files_to_remove = [
        CHECKPOINT_FILE,
        CSV_FILE,
        "wikidata_cache.json"
    ]
    print("🧹 Cleaning cache and temporary files...")
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"  - Deleted: {file}")


if __name__ == "__main__":
    asyncio.run(main(start_year=start_year, end_year=end_year, batch_size=batch_size))


'''
import pandas as pd
dd = pd.read_csv("ukrainian_history_data_batched_temp2.csv", encoding="utf-8", encoding_errors="replace")
print(dd.shape, dd.WikipediaURL.nunique())

dd = dd.drop_duplicates(['WikipediaURL'])
dd.BirthPlace = dd.BirthPlace.fillna('')
dd[dd.BirthPlace=='Едмонтон'].shape
dd[dd.BirthPlace=='Київ'].shape

dd[dd.PersonName=='Ференцевич Юрій']

dd['Year'] = dd['BirthDate'].apply(extract_year)
dd[dd.Year==1926].shape



#dd2 = pd.read_excel("../ukraininans_wiki_data_description.xlsx")
dd2 = pd.read_csv('../wiki_data_ukr_all.csv')
dd2 = dd2.drop_duplicates(['WikipediaURL'])
print(dd2.shape, dd2.WikipediaURL.nunique())

dd2.BirthPlace = dd2.BirthPlace.fillna('')
dd2[['PersonName', 'BirthPlace']].head()

dd2[dd2.BirthPlace=='Едмонтон'].shape
dd2[dd2.BirthPlace=='Львів'].shape

from datetime import datetime

def extract_year(date_str):
    try:
        # Адаптуйте формат під ваші дані, наприклад, '%Y-%m-%d'
        # Беремо перші 10 символів, щоб відсікти 'T00:00:00Z'
        clean_date = str(date_str)[:10] 
        return datetime.strptime(clean_date, '%Y-%m-%d').year
    except Exception:
        return None

dd2['Year'] = dd2['BirthDate'].apply(extract_year)

s1 = set(dd2[dd2.Year==1926].PersonName.tolist())
s2 = set(dd[dd.Year==1926].PersonName.tolist())


dd2[dd2.BirthPlace=='Едмонтон'].shape
dd2[dd2.BirthPlace=='Львів'].shape

dd2[dd2.PersonName=='Ягодзінський Аполлон Григорович'].PersonName

s = 'Едмонтон'
d1 = dd[dd.BirthPlace==s].PersonName.tolist()
d2 = dd2[dd2.BirthPlace==s].PersonName.tolist()
set(d2)-set(d1)
print(len(set(d1)), len(set(d2)))
'''


import pandas as pd
from config import CSV_FILE

# 1. Читаємо наявний файл
data = pd.read_csv(CSV_FILE)

# 2. Створюємо новий рядок як DataFrame
new_row = pd.DataFrame([{
    "PersonName": "Мельник Юрій Володимирович",
    "BirthPlace": "Олесько",
    "BirthDate": "1967-03-26",
    "Coordinates": "Point(24.901267 49.961157)",
    "DeathPlace": "Броди",
    "Coordinates_death": "Point(25.151739 50.082806)",
    "DeathDate": "2023-10-10",
    "WikipediaURL": "https://uk.wikipedia.org/wiki/%D0%9C%D0%B5%D0%BB%D1%8C%D0%BD%D0%B8%D0%BA_%D0%AE%D1%80%D1%96%D0%B9_%D0%92%D0%BE%D0%BB%D0%BE%D0%B4%D0%B8%D0%BC%D0%B8%D1%80%D0%BE%D0%B2%D0%B8%D1%87_(%D0%B2%D1%87%D0%B8%D1%82%D0%B5%D0%BB%D1%8C)",
    "Sex": "чоловіча",
    "Description": "Директор Бродівської гімназії ім. Івана Труша, вчитель, педагог, краєзнавець",
    "WikiText": "Юрій Володимирович Мельник (26 березня 1967, смт Олесько, Буський район, Львівська область — 10 жовтня 2023, м. Броди, Львівська область) — український педагог, краєзнавець, директор Бродівської гімназії імені Івана Труша (2020—2023).",
    "Occupation": "Директор, вчитель, педагог",
    "Field": "",
    "Position": "",
    "Ethnicity": "українець",
    "IsCitizen": "Україна",
    "IsEthnic": "Україна",
    "BornEntity": "",
    "BornSpatial": "",
    "IsTextMatch": "",
    "IsSpeaker": "Yes",
    "IsAncestry": ""
}])

# 3. Об'єднуємо (ігноруємо індекс, щоб він продовжився автоматично)
data = pd.concat([data, new_row], ignore_index=True)

# 4. Не забудьте зберегти оновлений CSV, якщо це потрібно:
data.to_csv(CSV_FILE, index=False)