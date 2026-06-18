import pandas as pd
import os

def search_csv(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
    
    try:
        df = pd.read_csv(filename)
        found = df[df["PersonName"].str.contains("Ференцевич", na=False)]
        if not found.empty:
            print(f"Found in {filename}:")
            print(found[["PersonName", "BirthDate", "BirthPlace"]])
        else:
            print(f"Not found in {filename}.")
    except Exception as e:
        print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    search_csv("ukrainian_history_data_batched1111.csv")
    search_csv("ukrainian_history_data_batched.csv")
    search_csv("ukrainian_history_data_batched_bkp.csv")
