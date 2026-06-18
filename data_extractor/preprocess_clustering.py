import asyncio
import os
import json
import warnings
import sys
import time

import pandas as pd
from pathlib import Path
from datetime import datetime
from config import CHECKPOINT_FILE, CSV_FILE

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 30)



data = pd.read_csv(CSV_FILE)
data.Description = data.Description.fillna("").astype(str)

# Використовуємо .copy(), щоб уникнути SettingWithCopyWarning
df_clustering = data[data.Description != ''][['PersonName','BirthPlace','Description','WikipediaURL','WikiText']].copy()

print('Before:', data.shape[0], 'After:', df_clustering.shape[0])

# 1. Видаляємо текст у дужках
df_clustering['Description'] = df_clustering['Description'].str.replace(r'\(.*?\)', '', regex=True)

# 2. Очищення: залишаємо літери (укр + латиниця), пробіли та коми!
# Заміняємо крапки та крапки з комою на звичайну кому
df_clustering['Description'] = df_clustering['Description'].str.replace(r'[.;]', ',', regex=True)
# Видаляємо всі інші спецсимволи, залишаючи літери, цифри, пробіли, коми та дефіси
df_clustering['Description'] = df_clustering['Description'].str.replace(r'[^а-яА-ЯҐґЄєІіЇїa-zA-Z0-9\s,\-]', '', regex=True)

# 3. Очищаємо від зайвих пробілів та ком
df_clustering['Description'] = (
    df_clustering['Description']
    .str.replace(r'\s+', ' ', regex=True)       # множинні пробіли -> один
    .str.replace(r'\s+,', ',', regex=True)      # "пробіл кома" -> "кома"
    .str.replace(r',+', ',', regex=True)        # множинні коми -> одна
    .str.strip(', ')                            # прибираємо коми/пробіли на краях
)


df_clustering['embedding_text'] = df_clustering.Description

# Додаткове очищення фінального тексту ембедінгів
df_clustering['embedding_text'] = (
    df_clustering['embedding_text']
    .str.replace(r'\s+', ' ', regex=True)
    .str.replace(r',+', ',', regex=True)
    .str.strip(', ')
)

df_clustering = df_clustering[df_clustering.embedding_text !='']

df_clustering.to_csv('wiki_data_ukr_clustering_new.csv', index=False)