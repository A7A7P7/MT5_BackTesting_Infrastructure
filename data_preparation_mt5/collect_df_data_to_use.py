#%%

import datetime
import MetaTrader5 as mt5
import pytz
import pandas as pd

#%%

from data_clean import data_cleaner
from data_inspect import data_inspection_tfs_adjustments
from data_load import data_loader
from data_store_fetch_cache import data_store_fetch_cache

#%%

def get_m1_symbol_data(symbol,start_date:datetime.datetime) -> pd.DataFrame: #GET DF M1 OF A SYMBOL SINCE START DATE

    tz_utc = pytz.UTC
    batch_end_date = datetime.datetime(year=start_date.year+1,month=3,day=9,tzinfo=tz_utc)
    current_year = datetime.date.today().year
    all_years_df_m1 = pd.DataFrame()

    while batch_end_date.year <= current_year:

        df_m1 = data_loader.mt5_import_to_df(symbol,tf_m1,start_date,batch_end_date)
        df_m1 = data_cleaner.df_m1_cleaning(df_m1)
        dic_stats_df = data_inspection_tfs_adjustments.missing_candles_m1_ny_time(df_m1)
        df_m1 = dic_stats_df['df_m1']
        if len(all_years_df_m1) == 0:
            all_years_df_m1 = df_m1
        else:
            last_date_all_years = all_years_df_m1.at[all_years_df_m1.index[-1],"Date"]
            start_date_df_m1 = df_m1.at[0,"Date"]
            if last_date_all_years == start_date_df_m1:
                df_m1 = df_m1.loc[1:,:]
                all_years_df_m1 = pd.concat([all_years_df_m1,df_m1],axis=0,ignore_index=True)
            else:
                all_years_df_m1 = pd.concat([all_years_df_m1,df_m1],axis=0,ignore_index=True)
        
        start_date = batch_end_date
        batch_end_date = datetime.datetime(year=start_date.year+1,month=3,day=9,tzinfo=tz_utc)
        while batch_end_date.weekday() != 6:

            batch_end_date_ordinal = batch_end_date.toordinal()
            batch_end_date_ordinal_test = batch_end_date_ordinal - 1
            batch_end_date = datetime.datetime.fromordinal(batch_end_date_ordinal_test)
    
    return all_years_df_m1

def get_working_df():

    fetch_from_mt5_or_cache = int(input("DO YOU WANT TO FETCH M1 DATA FROM MT5 CONNECTION (ANSWER 0) OR FROM YOUR OWN STORAGE (ANSWER 1): "))

    while fetch_from_mt5_or_cache != 0 and fetch_from_mt5_or_cache != 1:

        print("ANSWER 0 FOR FETCH FROM MT5 OR 1 IF YOU HAVE YOUR OWN STORAGE")
        fetch_from_mt5_or_cache = int(input("DO YOU WANT TO FETCH M1 DATA FROM MT5 CONNECTION (ANSWER 0) OR FROM YOUR OWN STORAGE (ANSWER 1): "))

    if fetch_from_mt5_or_cache == 0:
          
        fx_pair = str(input("PAIR TO FETCH FROM MT5 (EX: EURUSD,GBPUSD,EURGBP OR OTHER): ")).upper()
        year = int(input("STARTING YEAR FOR FETCHING: "))
        month = int(input("STARTING MONTH FOR FETCHING: "))
        day = int(input("STARTING DAY FOR FETCHING: "))
        date = datetime.datetime(year=year,month=month,day=day)
        while date.weekday() != 6:

            day = int(input("CHOOSE ANOTHER DAY FOR START FETCHING: "))
            date = datetime.datetime(year=year,month=month,day=day)
    
        start_date = data_loader.ensure_sunday_date(date)
        df_m1 = get_m1_symbol_data(fx_pair,start_date)

    else: #ANSWER IS 1 AND FETCH FROM STORAGE

        directory_root = str(input("DIRECTORY WHERE YOU HAVE ALL THE FX PAIRS: ")).strip().strip('"').strip("'")
        fx_pair = str(input("PAIR TO FETCH FROM STORAGE (EX: EURUSD,GBPUSD,EURGBP OR OTHER): ")).upper()
        df_m1 = data_store_fetch_cache.read_parquet_to_df(directory_root,fx_pair)
    
    return df_m1

#%%

df_m1_for_test = get_working_df()