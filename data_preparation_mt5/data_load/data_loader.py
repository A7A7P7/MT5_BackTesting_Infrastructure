#%%
import datetime
import zoneinfo
import time
import pandas as pd
import numpy as np
import pytz
import MetaTrader5 as mt5
from pathlib import Path

# %%

"""ONLY WORK WITH DATA ON SUNDAYS TO GET FULL WEEKS OF DATA, STARTING AND ENDING AT WITH OTHER DATES WILL MESS THE EXTRACTION, NEVER USE SATURDAYS

EVERY MENTION TO TIME IS NY TIME

SUNDAY_2_MONDAY - STARTS AT SUNDAY OPENING AND CLOSES AT SUNDAY 19PM BEFORE THE MONDAY THAT CLOSES THE RANGE FROM WHERE ONE IS EXTRACTING DATA
SUNDAY_2_SUNDAY - FULL WEEK OF DATA - STARTS AT SUNDAY OPENING AND ENDS AT THE FRIDAY CLOSE OF THE CLOSEST FRIDAY TO THE SUNDAY ENDING THE DATA RANGE;
SUNDAY_2_ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY - STARTS AT SUNDAY OPENING AND ENDS AT THE DAY BEFORE (ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY) AT 19PM

MONDAY_2_MONDAY - STARTS AT 19PM THE SUNDAY BEFORE THE MONDAY OF THE START OF THE RANGE AND ENDS AT SUNDAY 19PM BEFORE THE MONDAY THAT CLOSES THE RANGE
MONDAY_2_SUNDAY - STARTS AT 19PM THE SUNDAY BEFORE THE MONDAY OF THE START OF THE RANGE AND ENDS AT FRIDAY THAT PRECEDES THE SUNDAY OF THE FINAL OF THE RANGE AT THE CLOSING OF THE MARKET;
MONDAY_2_ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY - STARTS AT 19PM THE SUNDAY BEFORE THE MONDAY OF THE START OF THE RANGE AND ENDS AT AT THE DAY BEFORE (ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY) AT 19PM
   
ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY_2_MONDAY - STARTS AT 19PM THE DAY BEFORE THE (ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY) AND ENDS AT SUNDAY 19PM BEFORE THE MONDAY THAT CLOSES THE RANGE
ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY_2_SUNDAY - STARTS AT 19PM THE DAY BEFORE THE (ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY) AND ENDS AT FRIDAY THAT PRECEDES THE SUNDAY OF THE FINAL OF THE RANGE AT THE CLOSING OF THE MARKET;
ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY_2_ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY - STARTS AT 19PM THE DAY BEFORE THE (ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY) AND ENDS AT AT THE DAY BEFORE (ANOTHER_DAY_BUT_MONDAY_OR_SUNDAY) AT 19PM

"""
#%%

def ensure_sunday_date(date: datetime.datetime) -> datetime.datetime:

    if date.weekday() != 6:
        raise ValueError('⚠️⚠️⚠️Date must be Sunday⚠️⚠️⚠️')
    return date

#%%

"""LOAD OF DATA AND TRANSFORMATION INTO DF"""

def mt5_import_to_df(fx_pair,timeframe,start_date,end_date):

    # establish connection to MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()

    rates = mt5.copy_rates_range(fx_pair, timeframe, start_date, end_date)

    # shut down connection to the MetaTrader 5 terminal
    mt5.shutdown()

    #TRANSFORMATION
    rates_frame = pd.DataFrame(rates)
    # convert time in seconds into the datetime format
    rates_frame["time"] = pd.to_datetime(rates_frame["time"], unit='s')
    rates_frame["time"] = rates_frame["time"] - pd.Timedelta(hours=2) - pd.Timedelta(hours=5) #FIRST 2 TO ADJUST THE OPENING, NEXT 5 TO PUT NY TIME
    rates_df_to_work = rates_frame.loc[:,["time","open","high","low","close","spread","tick_volume", "real_volume"]]
    cols_name = ["Date","Open","High","Low","Close","Spread","Tick_Volume","Real_Volume"]
    rates_df_to_work.columns = cols_name

    return rates_df_to_work
    


