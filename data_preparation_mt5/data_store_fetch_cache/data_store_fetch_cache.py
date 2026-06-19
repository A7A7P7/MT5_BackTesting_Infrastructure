#%%

import pandas as pd
from pathlib import Path

#%%

def store_in_parquet_m1_dataset(directory_for_storage:str,df_m1:pd.DataFrame):

    pair_to_cache = str(input("PAIR TO STORE (EX: EURUSD,GBPUSD,EURGBP OR OTHER): ")).upper()

    #CREATE DIR IF IT DOESN'T EXIST
    Path(rf"{directory_for_storage}/{pair_to_cache}_M1_CACHING").mkdir(exist_ok=True)
    directory = Path(rf"{directory_for_storage}/{pair_to_cache}_M1_CACHING")
    directory.mkdir(exist_ok=True)
    end_point = directory / rf"{pair_to_cache}.parquet"

    df_m1.to_parquet(end_point,engine="pyarrow",index=True)

#%%

def read_parquet_to_df(directory_stored:str,fx_pair:str):

    fx_pair = fx_pair.upper()
    lvl_below_main_dir = rf"{fx_pair}_M1_CACHING"
    for file in Path(rf"{directory_stored}\{lvl_below_main_dir}").iterdir():

        pair = file.stem
        if pair == fx_pair:

            df_m1 = pd.read_parquet(file)
    
    return df_m1