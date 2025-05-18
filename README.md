# Ukrainian Wikipedia Articles Interactive Visualization
This repository contains a python code which extracts locations of birth and death of ukrainians which have an wikipedia article. 
This application takes into account wikipedia peges where specified nationality, affiliation or birth place of countries:
- Ukraine
- Ukrainian Soviet Socialist Republic
- Ukrainian People's Republic (UPR)
- West Ukrainian People's Republic
- Cossack Hetmanate
- Kingdom of Galicia–Volhynia
- Kyivan Rus

### 👥 How Individuals Are Selected
- Type: The entity must be a human (wdt:P31 wd:Q5 – "instance of human").

- Origin: Defines the connection to Ukraine either through citizenship or place of birth. In other words, individuals must either have had citizenship of a historical or modern Ukrainian state (wdt:P27), or have been born in a place that belonged to one of the specified entities (wdt:P19 → wdt:P17).

- Required Condition: There must be an existing article about the person in the Ukrainian Wikipedia.
  

In ukrainians_wiki_articles.ipynb possible to create an application with intercative visualization maps where are possible to see a distrubution and hover over points to see detailed information.
Use zoom, scrolling and hover over points to interact with map.

### Application contains three pages:
 - Народження (page with interactive map with distribution of birth location, if it specified)
 - Смерть (page with interactive map with distribution of death location, if it specified)
 - Статистика (page with statistics by gender, distance between birth and death locations)
 - Інфо (information about SPARQL request)


**To reproduce results, firsly run:**
```
pip install -r requirements.txt
```

**Launch jupyter notebook from cmd:**
```
jupyter notebook
```

Here it is possibe manually interact with wiki data using SPARQL:
* https://query.wikidata.org/

<hr>

### Interactive Map
https://raw.githack.com/romario076/ukrainians_wikimap/refs/heads/main/ukrainians_wikimap.html

Hove over data points to see additional information or click to open respective wikipedia page.

### Example:
<img width="953" alt="image" src="https://github.com/user-attachments/assets/e465169e-e997-4ffd-9d9c-beb77973d047" />

<hr>

