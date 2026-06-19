#%%

import pandas as pd
import numpy as np
import datetime

#%%

def df_m1_cleaning(df: pd.DataFrame) -> pd.DataFrame:

    df['Day&Datetime'] = df['Date'].dt.date
    df['Week_day'] = df['Date'].dt.weekday
    df['Hour_of_Day'] = df['Date'].dt.hour
    df["Minute_of_Hour"] = df['Date'].dt.minute
    mask_remove = (
    (df['Date'].dt.weekday == 5) |  # Saturday
    ((df['Date'].dt.weekday == 6) & (df['Date'].dt.hour < 17)) | # Sundays before 17 NY TIME
    ((df['Date'].dt.weekday == 4) & (df['Date'].dt.hour >= 17)) |  # Fridays after 17 NY TIME
    (df[['Open','High','Low','Close']].nunique(axis=1) == 1) # nunique is the number of different values within the columns used
    )
    df = df[~mask_remove].reset_index(drop=True) #~ not here means that new df will only include stuff that isn't in the mask
    df['Is_Duplicated_Row'] = df[['Open','High','Low','Close']].duplicated()
    #Check if First and Last Candle are True
    condition_1 = df.at[1,'Is_Duplicated_Row'] == True
    condition_2 = df.at[len(df)-1,'Is_Duplicated_Row'] == True
    if condition_1 and condition_2:

        df = df[1:len(df)-2].reset_index(drop=True)
    
    elif condition_1 == False and condition_2:

        df = df[:len(df)-2].reset_index(drop=True)
    
    elif condition_1 and condition_2 == False:

        df = df[1:].reset_index(drop=True)
    
    #RE-ORDERING OF COLUMNS
    df=df[['Date','Day&Datetime','Week_day','Hour_of_Day','Minute_of_Hour','Open','High','Low','Close','Is_Duplicated_Row']]
    #df = df[~df['Is_Duplicated_Row']].reset_index(drop=True) #keeps columns where 'Is_Duplicated_Row' is False
    
    return df

#%%

"""ONLY USABLE AFTER DATA INSPECTION ADJUSTMENTS IS MADE AND BEEFORE STRUCTURE IS USED"""

def remove_unprintable_rows(df: pd.DataFrame): 

    return df[df['Candle_Can_Be_Printed'] == True]


# %%
