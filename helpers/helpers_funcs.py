#%%
import pandas as pd
import numpy as np
from datetime import datetime

#%%

def number_timeframes_used() -> int:

    print("Number_of_Timeframes SHOULD BE ABOVE 0 AND BELOW 5")

    n_timeframes = int(input("HOW MANY TIMEFRAMES YOU WANT TO USE: "))

    if 0 < n_timeframes < 5:

        print(f"{n_timeframes} HAVE BEEN CHOSEN")
        return n_timeframes
    
    else:

        if n_timeframes <= 0:

            raise ValueError("Number_of_Timeframes CANNOT BE BELOW 0")

        else:

            raise ValueError("TOO MANY TIMEFRAMES") 

#%%

def timeframes_chosen(n_of_timeframes:int) -> dict:

    print("CHOOSE THE TIMEFRAMES IN ORDER OFF TIME FROM SMALLEST TO BIGGEST")

    dic_timeframes = dict()

    for i in range(n_of_timeframes):

        print(f"{i+1}ST TIMEFRAME IS BEING CHOOSEN")

        if i == 0:

            n_of_minutes = int(input("Nº OF MINUTES IN YOUR TIMEFRAME Nº1"))
            rest_eq_zero_below_60 = 60 % n_of_minutes == 0 #VALUES BELOW 60
            rest_eq_zero_above_60 = n_of_minutes % 60 == 0 #VALUES ABOVE 60

            if rest_eq_zero_above_60 or rest_eq_zero_below_60:

                if rest_eq_zero_below_60:

                    dic_timeframes[f"m{n_of_minutes}"] = n_of_minutes
                
                else:

                    dic_timeframes[f"h{int(n_of_minutes/60)}"] = n_of_minutes
            
            else:

                combined_cond = rest_eq_zero_above_60 or rest_eq_zero_below_60
                while combined_cond == False:

                    print("Nº of minutes needs to be either a MULTIPLE off 60 or DIVISABLE by 60")
                    n_of_minutes = int(input("Nº OF MINUTES IN YOUR TIMEFRAME Nº1"))
                    rest_eq_zero_below_60 = 60 % n_of_minutes == 0 #VALUES BELOW 60
                    rest_eq_zero_above_60 = n_of_minutes % 60 == 0 #VALUES ABOVE 60
                    combined_cond = rest_eq_zero_above_60 or rest_eq_zero_below_60

                if rest_eq_zero_below_60:

                    dic_timeframes[f"m{n_of_minutes}"] = n_of_minutes
                
                else:

                    dic_timeframes[f"h{int(n_of_minutes/60)}"] = n_of_minutes
        
        else:

            minutes_prev_tf = list(dic_timeframes.values())[-1]
            print(f"{i+1}ST TIMEFRAME IS BEING CHOOSEN")

            n_of_minutes = int(input(f"Nº OF MINUTES IN YOUR TIMEFRAME Nº{i+1}"))
            higher_tf_than_last = n_of_minutes > minutes_prev_tf
            rest_eq_zero_below_60 = 60 % n_of_minutes == 0 #VALUES BELOW 60
            rest_eq_zero_above_60 = n_of_minutes % 60 == 0 #VALUES ABOVE 60

            tf_approve = higher_tf_than_last and (rest_eq_zero_below_60 or rest_eq_zero_above_60)

            if tf_approve:

                if rest_eq_zero_below_60:

                    dic_timeframes[f"m{n_of_minutes}"] = n_of_minutes
                
                else:

                    dic_timeframes[f"h{int(n_of_minutes/60)}"] = n_of_minutes
            
            else:

                while tf_approve == False:

                    print(f"Nº of minutes needs to be HIGHER than {minutes_prev_tf} AND either a MULTIPLE off 60 or DIVISABLE by 60")
                    n_of_minutes = int(input(f"Nº OF MINUTES IN YOUR TIMEFRAME Nº{i+1}"))
                    higher_tf_than_last = n_of_minutes > minutes_prev_tf
                    rest_eq_zero_below_60 = 60 % n_of_minutes == 0 #VALUES BELOW 60
                    rest_eq_zero_above_60 = n_of_minutes % 60 == 0 #VALUES ABOVE 60
                    tf_approve = higher_tf_than_last and (rest_eq_zero_below_60 or rest_eq_zero_above_60)
                
                if rest_eq_zero_below_60:

                    dic_timeframes[f"m{n_of_minutes}"] = n_of_minutes
                
                else:

                    dic_timeframes[f"h{int(n_of_minutes/60)}"] = n_of_minutes
    
    return dic_timeframes

def dict_all_engines(lst_tf_engines:list,timeframes_used:dict) -> dict:

    dic_all_engines = dict()
    tf_keys = list(timeframes_used.keys())
    for i in range(len(lst_tf_engines)):

        dic_all_engines[tf_keys[i]] = lst_tf_engines[i]
    
    return dic_all_engines

#%%

def dict_buffers(timeframes_used:dict) -> dict:

    tf_keys = list(timeframes_used.keys())
    dic_buffer = dict()

    for i in range(len(timeframes_used)):

        if i == 0:

            if timeframes_used[tf_keys[i]] != 1:

                dic_buffer[tf_keys[i]] = list()
        
        else:

            dic_buffer[tf_keys[i]] = list()
    
    return dic_buffer

#%%

def dict_timeframes(timeframes_used:dict) -> dict:

    tf_keys = list(timeframes_used.keys())
    dict_timeframes = dict()

    for i in range(len(timeframes_used)):

        if i == 0:

            if timeframes_used[tf_keys[i]] != 1:

                dict_timeframes[tf_keys[i]] = dict()
                dict_timeframes[tf_keys[i]]["ratio"] = timeframes_used[tf_keys[i]]
        
        else:

            dict_timeframes[tf_keys[i]] = dict()
            dict_timeframes[tf_keys[i]]["ratio"] = timeframes_used[tf_keys[i]]

    return dict_timeframes

#%%

def dict_next_opens(timeframes_used:dict) -> dict:

    tf_keys = list(timeframes_used.keys())
    dic_next = dict()

    for i in range(len(timeframes_used)):

        if i == 0:

            if timeframes_used[tf_keys[i]] != 1:

                dic_next[tf_keys[i]] = None
        
        else:

            dic_next[tf_keys[i]] = None
    
    return dic_next

#%%

def latest_setup(timeframes_used:dict) -> dict:

    tf_keys = list(timeframes_used.keys())
    dic_latest = dict()

    for i in range(len(timeframes_used)):

        dic_latest[tf_keys[i]] = None
    
    return dic_latest

#%%

def struct_when_trade(timeframes_used:dict) -> dict:

    tf_keys = list(timeframes_used.keys())
    dic_trade = dict()

    for i in range(len(timeframes_used)):

        dic_trade[tf_keys[i]] = list()
    
    return dic_trade






