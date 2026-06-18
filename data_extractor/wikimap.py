import re
import json
import time
import numpy as np
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm
#from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from itertools import chain
import pydeck as pdk
from bs4 import BeautifulSoup

from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

from config import CHECKPOINT_FILE, CSV_FILE

import warnings
warnings.filterwarnings(action='ignore')

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 30)


def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in kilometers
    R = 6371.0

    lat1, lon1 = map(math.radians, (lat1,lon2))
    lat2, lon2 = map(math.radians, (lat2,lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in kilometers



df = pd.read_csv('../wiki_data_ukr_all.csv', nrows=100)
df = df.drop_duplicates(['PersonName','WikipediaURL'])
print('Dataframe size: ', df.shape)


### Columns manipulation
def is_valid_date(date_string):
    try:
        pd.Timestamp(date_string)
        return True
    except ValueError:
        return False

def convert_to_date(date_string):
    try:
        return str(pd.Timestamp(date_string).date())
    except:
        return 'не вказано'

### For bithdate dataframe
df['Lon'] = [float(re.findall(r"Point\((-?\d+.\d+)", x)[0]) for x in df.Coordinates]
df['Lat'] = [float(re.findall(r"Point\(-?\d+.\d+\s+(-?\d+.\d+)", x)[0]) for x in df.Coordinates]
df['Birthday'] = [convert_to_date(x) for x in df.BirthDate]

cord_df = df[['Lat','Lon','PersonName','BirthPlace','Birthday', 'Sex','WikipediaURL','Affiliation']]


### Calculate distance

### Define death dataframe
df_death = df[df.DeathPlace!='']

### For deathday dataframe
df_death.Coordinates_death = df_death.Coordinates_death.fillna('')
df_death = df_death[df_death.Coordinates_death.str.contains('Point')]
df_death['Lon'] = [float(re.findall(r"Point\((-?\d+.\d+)", x)[0]) for x in df_death.Coordinates]
df_death['Lat'] = [float(re.findall(r"Point\(-?\d+.\d+\s+(-?\d+.\d+)", x)[0]) for x in df_death.Coordinates]
df_death['Lon_death'] = [float(re.findall(r"Point\((-?\d+.\d+)", x)[0]) for x in df_death.Coordinates_death]
df_death['Lat_death'] = [float(re.findall(r"Point\(-?\d+.\d+\s+(-?\d+.\d+)", x)[0]) for x in df_death.Coordinates_death]
df_death['Birthday'] = [convert_to_date(x) for x in df_death.BirthDate]
df_death['DeathDate'] = [convert_to_date(x) for x in df_death.DeathDate]
df_death['Distance'] = [haversine(x1,y1, x2,y2) for x1,y1,x2,y2 in zip(df_death.Lat,df_death.Lon, df_death.Lat_death,df_death.Lon_death)]
df_death['SamePlace'] = np.where(df_death.BirthPlace==df_death.DeathPlace, 1, 0)

df_death = df_death.drop(['Lat','Lon'], axis=1)
df_death = df_death.rename(columns={'Lat_death':'Lat', 'Lon_death':'Lon'})
df_death = df_death[['Lat','Lon','PersonName','Birthday','BirthPlace','DeathDate','DeathPlace','Distance','SamePlace', 'Sex','WikipediaURL','Affiliation']]
