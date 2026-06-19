import pandas as pd
import numpy as np
import datetime


#%%


def missing_candles_m1_ny_time(df_m1: pd.DataFrame) -> dict: #H1 as Base and only DFs above H1

    #Get a counter of how many days of the week from the start_date to end_date through usage off ordinals by assigning a weekday to each ordinal.
    candles_per_day = []
    count_candles = 1
    days_of_week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    days_of_the_week_count = [0,0,0,0,0,0,0]
    for n in range(1,len(df_m1)):
        candle_before_date = df_m1.at[n-1,'Day&Datetime']
        current_candle_date = df_m1.at[n,'Day&Datetime']
        if candle_before_date != current_candle_date:
            candles_per_day.append([candle_before_date,f'Candles_on_day: {count_candles}',f'Index of final candle of the day: {n-1}',f'{days_of_week[candle_before_date.weekday()]}'])
            days_of_the_week_count[candle_before_date.weekday()] += 1
            count_candles = 1
        else:
            count_candles += 1
    days_of_the_week_count[df_m1.at[len(df_m1)-1,'Day&Datetime'].weekday()] += 1

    total_trading_minutes_in_df = len(df_m1)
    total_trading_minutes_in_date_range = days_of_the_week_count[0] * 24*60 + days_of_the_week_count[1] * 24*60 + days_of_the_week_count[2] * 24*60 + days_of_the_week_count[3] * 24*60 + days_of_the_week_count[4] * 17*60 + days_of_the_week_count[6] * 7*60

    if total_trading_minutes_in_df == total_trading_minutes_in_date_range:

        print('✅✅✅DIFFERENT TIMEFRAMES CANDLES MATCH & ALL DAYS THAT DF FETCHED HAVE FULL DATA')

        return {'data_missing_candles' : None, 
                'total_trading_minutes_in_date_range' : total_trading_minutes_in_date_range,
                'days_of_the_week_count' : days_of_the_week_count,
                'total_trading_minutes_in_df' : total_trading_minutes_in_df,
                'df_m1' : df_m1
                }
    
    else:

        print('⚠️⚠️⚠️DIFFERENT TIMEFRAMES CANDLES MATCHING SUFFERED ADJUSTMENTS, DATA ON SOME DAYS MIGHT BE LACKING\n')
        data_missing_candles = []
        for i in range(len(candles_per_day)):

            dict_hours_minutes = dict()
            hours_missing = []
            cond_1 = candles_per_day[i][1] != 'Candles_on_day: 1440'
            cond_2 = candles_per_day[i][1] != 'Candles_on_day: 420'
            cond_3 = candles_per_day[i][1] != 'Candles_on_day: 1020'

            if cond_1 and cond_2 and cond_3:

                df_of_day = df_m1[df_m1['Day&Datetime'] == candles_per_day[i][0]].reset_index(drop=True)
                hours_list = df_of_day['Hour_of_Day'].tolist()
                        
                if candles_per_day[i][3] == 'Sunday':

                    for hour in range(17,24):

                        if hour not in hours_list:

                            hours_missing.append(hour)
                            lst_minutes_missing_in_hour = [i for i in range(0,60)]
                            dict_hours_minutes[f"Entire Hour {hour} Missing"] = lst_minutes_missing_in_hour
                                
                        else:

                            df_of_hour = df_of_day[df_of_day['Hour_of_Day'] == hour].reset_index(drop=True)
                            minutes_list = df_of_hour['Minute_of_Hour'].tolist()
                            lst_minutes_missing_in_hour = []

                            for minute in range(0,60):
                                
                                if minute not in minutes_list:

                                    lst_minutes_missing_in_hour.append(minute)
                            
                            if len(lst_minutes_missing_in_hour) != 0:

                                dict_hours_minutes[f"Missing Minutes in Hour {hour}"] = lst_minutes_missing_in_hour
    
                elif candles_per_day[i][3] == 'Friday':

                    for hour in range(0,17):

                        if hour not in hours_list:

                            hours_missing.append(hour)
                            lst_minutes_missing_in_hour = [i for i in range(0,60)]
                            dict_hours_minutes[f"Entire Hour {hour} Missing"] = lst_minutes_missing_in_hour
                        
                        else:

                            df_of_hour = df_of_day[df_of_day['Hour_of_Day'] == hour].reset_index(drop=True)
                            minutes_list = df_of_hour['Minute_of_Hour'].tolist()
                            lst_minutes_missing_in_hour = []

                            for minute in range(0,60):
                                
                                if minute not in minutes_list:

                                    lst_minutes_missing_in_hour.append(minute)
                            
                            if len(lst_minutes_missing_in_hour) != 0:

                                dict_hours_minutes[f"Missing Minutes in Hour {hour}"] = lst_minutes_missing_in_hour
                        
                else: #Monday,Tuesday,Wednesday,Thursday
                        
                    for hour in range(0,24):

                        if hour not in hours_list:

                            hours_missing.append(hour)
                            lst_minutes_missing_in_hour = [i for i in range(0,60)]
                            dict_hours_minutes[f"Entire Hour {hour} Missing"] = lst_minutes_missing_in_hour
                        
                        else:

                            df_of_hour = df_of_day[df_of_day['Hour_of_Day'] == hour].reset_index(drop=True)
                            minutes_list = df_of_hour['Minute_of_Hour'].tolist()
                            lst_minutes_missing_in_hour = []

                            for minute in range(0,60):
                                
                                if minute not in minutes_list:

                                    lst_minutes_missing_in_hour.append(minute)
                            
                            if len(lst_minutes_missing_in_hour) != 0:

                                dict_hours_minutes[f"Missing Minutes in Hour {hour}"] = lst_minutes_missing_in_hour

                data_missing_candles.append([f'Date of candle(s) missing : {candles_per_day[i][0]}',candles_per_day[i][2],candles_per_day[i][3],f'Hours&Minutes_Missing : {dict_hours_minutes}'])
                #data_missing_candles each index has a list with
                    #date of candle missing
                    #Index of final candle of the day
                    #Day in the week
                    #hours of that day missing
                    #dict with uncompleted hours and minutes

        return {'data_missing_candles' : data_missing_candles if len(data_missing_candles) != 0 else None, 
                'total_trading_minutes_in_date_range' : total_trading_minutes_in_date_range,
                'days_of_the_week_count' : days_of_the_week_count,
                'total_trading_minutes_in_df' : total_trading_minutes_in_df,
                'df_m1' : df_m1
                }


def different_timeframe(df_m1,timeframe_mult):

    rebuild_df = pd.DataFrame()

    if (timeframe_mult < 1 or timeframe_mult > 24*60) or  (24*60 % timeframe_mult != 0): #24*60 the number of minutes in a day

        raise ValueError(
            "'timeframe_mult' NEEDS TO BE:\n"
            "1 <= 'timeframe_mult' <= 1440\n"
            "1440 DIVIDED BY 'timeframe_mult' MUST YIELD A NATURAL NUMBER"
        )

    else:

        #ADJUSTMENT ON WHICH CANDLES ARE USED TO START THE DF
        idx = 0
        minute_of_hour = df_m1.at[idx,"Minute_of_Hour"]

        while minute_of_hour != 0:

            idx += 1
            minute_of_hour = df_m1.at[idx,"Minute_of_Hour"]
        
        df_m1 = df_m1[idx:].reset_index(drop=True)

        lst_of_datetimes = [df_m1.at[0,'Date']]
        all_dates = [df_m1.at[0,'Date']]
        #'lst_of_datetimes' HAS THE SUPPOSED DATES TO BE FILLED, NOT DEPENDENT ON df_m1
        while all_dates[-1] < df_m1.at[len(df_m1)-1,'Date']: #CAPTURE ALL THE DATA POINTS OF TIMEFRAME_MULT WITHIN THE RANGES USED

            #HERE THERE ARE NO PROBLEMS WITH TIMEZONES SO IT IS OKAY TO JUST APPEND
            date_to_append = all_dates[-1] + pd.Timedelta(minutes=timeframe_mult)
            all_dates.append(date_to_append)
            """date_to_append = all_dates[-1] + datetime.timedelta(hours=timeframe_mult)"""

            if (date_to_append.weekday() == 5) or (date_to_append.weekday() == 4 and date_to_append.hour > 16) or (date_to_append.weekday() == 6 and date_to_append.hour < 17):
                all_dates.append(date_to_append) #HOURS IN WHICH FX MARKET IS CLOSED.
            else: #DATES WHERE FX MARKET IS OPEN
                all_dates.append(date_to_append)
                lst_of_datetimes.append(date_to_append)

        for ind in range(1,len(lst_of_datetimes)):

            date = lst_of_datetimes[ind-1]
            #CHECK IF THE DATE IN 'lst_of_datetimes' EXISTS IN df_m1
            if df_m1['Date'].eq(lst_of_datetimes[ind-1]).any():

                #FIRST DATE OF THE CANDLE TO BE FORMED
                first_index_recurring_range = df_m1[df_m1['Date'] == date].index[0]

                if df_m1['Date'].eq(lst_of_datetimes[ind]).any(): #SEE IF LAST MINUTE CANDLE OF THE NEW TF CANDLE EXISTS, HERE EXISTS

                    last_index_recurring_range = df_m1[df_m1['Date'] == lst_of_datetimes[ind]].index[0]

                    working_df = df_m1[first_index_recurring_range:last_index_recurring_range].copy()
                    open = working_df.at[first_index_recurring_range,'Open']
                    high = max(working_df['High'])
                    low = min(working_df['Low'])
                    close = working_df.at[last_index_recurring_range-1,'Close']
                    #GET WHAT 'minutes' ARE MISSING
                    minutes = 0 
                    minutes_missing = []
                    while minutes < timeframe_mult:

                        if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                            minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                            minutes += 1

                        else: #SPECIFIC MINUTE EXISTS

                            minutes += 1

                    df_to_concat = pd.DataFrame(data={
                        'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
                        'Candles_Transformation' : [f'M{timeframe_mult}'],
                        'Open': [open],
                        'High': [high],
                        'Low': [low],
                        'Close' : [close],
                        f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [len(working_df)],
                        'Candles_Missing_To_Print': [minutes_missing],
                        'Candle_Can_Be_Printed' : [True]
                        #'Volume' : [volume]
                    })

                    rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)
                
                else: #LAST EXTREME MINUTE DOESN'T EXISTS IN df_m1

                    minute_adjustment_first_extreme = lst_of_datetimes[ind-1]
                    minute_adjustment_last_extreme = lst_of_datetimes[ind]

                    while minute_adjustment_last_extreme > minute_adjustment_first_extreme and df_m1['Date'].eq(minute_adjustment_last_extreme).any() == False:

                        minute_adjustment_last_extreme = minute_adjustment_last_extreme - datetime.timedelta(minutes=1)

                    if minute_adjustment_last_extreme > minute_adjustment_first_extreme: #ADJUSTED CANDLE IS COMPOSED BY MORE THAN 1 CANDLE

                        last_index_recurring_range = df_m1[df_m1['Date'] == minute_adjustment_last_extreme].index[0]
                        working_df = df_m1[first_index_recurring_range:last_index_recurring_range+1].copy()
                        open = working_df.at[first_index_recurring_range,'Open']
                        high = max(working_df['High'])
                        low = min(working_df['Low'])
                        close = working_df.at[last_index_recurring_range,'Close']
                        #GET WHAT 'minutes' ARE MISSING
                        minutes = 0 
                        minutes_missing = []
                        while minutes < timeframe_mult:

                            if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                                minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                                minutes += 1

                            else: #SPECIFIC MINUTE EXISTS

                                minutes += 1

                        df_to_concat = pd.DataFrame(data={
                            'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
                            'Candles_Transformation' : [f'M{timeframe_mult}'],
                            'Open': [open],
                            'High': [high],
                            'Low': [low],
                            'Close' : [close],
                            f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [len(working_df)],
                            'Candles_Missing_To_Print': [minutes_missing],
                            'Candle_Can_Be_Printed' : [True]
                            #'Volume' : [volume]
                        })

                        rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)

                    else: #ADJUSTED CANDLE ONLY HAS ONE CANDLE AS minute_adjustment_last_extreme == minute_adjustment_first_extreme

                        single_candle_index = first_index_recurring_range
                        open = df_m1.at[single_candle_index,'Open']
                        high = df_m1.at[single_candle_index,'High']
                        low = df_m1.at[single_candle_index,'Low']
                        close = df_m1.at[single_candle_index,'Close']
                        #GET WHAT 'minutes' ARE MISSING
                        minutes = 0 
                        minutes_missing = []
                        while minutes < timeframe_mult:

                            if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                                minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                                minutes += 1

                            else: #SPECIFIC MINUTE EXISTS

                                minutes += 1

                        df_to_concat = pd.DataFrame(data={
                            'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
                            'Candles_Transformation' : [f'M{timeframe_mult}'],
                            'Open': [open],
                            'High': [high],
                            'Low': [low],
                            'Close' : [close],
                            f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [1],
                            'Candles_Missing_To_Print': [minutes_missing],
                            'Candle_Can_Be_Printed' : [True]
                            #'Volume' : [volume]
                        })
                        
                        rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)

            #M1_CANDLE OF SUPPOSED 'first_index_recurring_range' DOESN'T EXIST
            else:
                
                minute_adjustment_first_extreme = lst_of_datetimes[ind-1]

                while minute_adjustment_first_extreme < lst_of_datetimes[ind] and df_m1['Date'].eq(minute_adjustment_first_extreme).any() == False :

                    minute_adjustment_first_extreme = minute_adjustment_first_extreme + datetime.timedelta(minutes=1)
                
                if minute_adjustment_first_extreme < lst_of_datetimes[ind]: #ADJUSTED CANDLE EXISTS

                    first_index_recurring_range = df_m1[df_m1['Date'] == minute_adjustment_first_extreme].index[0]

                    if df_m1['Date'].eq(lst_of_datetimes[ind]).any(): #SEE IF LAST EXTREME HOUR EXISTS IN df_m1

                        last_index_recurring_range = df_m1[df_m1['Date'] == lst_of_datetimes[ind]].index[0]

                        working_df = df_m1[first_index_recurring_range:last_index_recurring_range].copy()
                        open = working_df.at[first_index_recurring_range,'Open']
                        high = max(working_df['High'])
                        low = min(working_df['Low'])
                        close = working_df.at[last_index_recurring_range-1,'Close']
                        #GET WHAT 'minutes' ARE MISSING
                        minutes = 0 
                        minutes_missing = []
                        while minutes < timeframe_mult:

                            if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                                minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                                minutes += 1

                            else: #SPECIFIC MINUTE EXISTS

                                minutes += 1

                        df_to_concat = pd.DataFrame(data={
                            'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
                            'Candles_Transformation' : [f'M{timeframe_mult}'],
                            'Open': [open],
                            'High': [high],
                            'Low': [low],
                            'Close' : [close],
                            f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [len(working_df)],
                            'Candles_Missing_To_Print': [minutes_missing],
                            'Candle_Can_Be_Printed' : [True]
                            #'Volume' : [volume]
                        })
                        rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)
                        
                    else: # THAT LAST EXTREME HOUR DOESN'T EXIST IN df_m1

                        minute_adjustment_last_extreme = lst_of_datetimes[ind]

                        while minute_adjustment_last_extreme > minute_adjustment_first_extreme and df_m1['Date'].eq(minute_adjustment_last_extreme).any() == False:

                            minute_adjustment_last_extreme = minute_adjustment_last_extreme - datetime.timedelta(minutes=1)

                        if minute_adjustment_last_extreme > minute_adjustment_first_extreme: #ADJUSTED CANDLE IS COMPOSED BY MORE THAN 1 CANDLE

                            last_index_recurring_range = df_m1[df_m1['Date'] == minute_adjustment_last_extreme].index[0]
                            working_df = df_m1[first_index_recurring_range:last_index_recurring_range].copy()
                            open = working_df.at[first_index_recurring_range,'Open']
                            high = max(working_df['High'])
                            low = min(working_df['Low'])
                            close = working_df.at[last_index_recurring_range-1,'Close']
                            #GET WHAT 'minutes' ARE MISSING
                            minutes = 0 
                            minutes_missing = []
                            while minutes < timeframe_mult:

                                if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                                    minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                                    minutes += 1

                                else: #SPECIFIC MINUTE EXISTS

                                    minutes += 1

                            df_to_concat = pd.DataFrame(data={
                                'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
                                'Candles_Transformation' : [f'M{timeframe_mult}'],
                                'Open': [open],
                                'High': [high],
                                'Low': [low],
                                'Close' : [close],
                                f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [len(working_df)],
                                'Candles_Missing_To_Print': [minutes_missing],
                                'Candle_Can_Be_Printed' : [True]
                                #'Volume' : [volume]
                            })

                            rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)

                        else: #ADJUSTED CANDLE ONLY HAS ONE CANDLE AS hour_adjustment_last_extreme == hour_adjustment_first_extreme

                            single_candle_index = first_index_recurring_range
                            open = df_m1.at[single_candle_index,'Open']
                            high = df_m1.at[single_candle_index,'High']
                            low = df_m1.at[single_candle_index,'Low']
                            close = df_m1.at[single_candle_index,'Close']
                            #GET WHAT 'minutes' ARE MISSING
                            minutes = 0 
                            minutes_missing = []
                            while minutes < timeframe_mult:

                                if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                                    minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                                    minutes += 1

                                else: #SPECIFIC MINUTE EXISTS

                                    minutes += 1

                            df_to_concat = pd.DataFrame(data={
                                'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
                                'Candles_Transformation' : [f'M{timeframe_mult}'],
                                'Open': [open],
                                'High': [high],
                                'Low': [low],
                                'Close' : [close],
                                f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [1],
                                'Candles_Missing_To_Print': [minutes_missing],
                                'Candle_Can_Be_Printed' : [True]
                                #'Volume' : [volume]
                            })
                        
                            rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)

                else: #ADJUSTED CANDLE DOESN'T EXIST  minutes_adjustment == lst_of_datetimes[ind]

                    #GET WHAT 'minutes' ARE MISSING
                    minutes = 0 
                    minutes_missing = []
                    while minutes < timeframe_mult:

                        if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                            minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                            minutes += 1

                        else: #SPECIFIC MINUTE EXISTS

                            minutes += 1

                    df_to_concat = pd.DataFrame(data={
                        'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
                        'Candles_Transformation' : [f'M{timeframe_mult}'],
                        'Open': [rebuild_df.at[len(working_df)-1,'Close']],
                        'High': [rebuild_df.at[len(working_df)-1,'Close']],
                        'Low': [rebuild_df.at[len(working_df)-1,'Close']],
                        'Close' : [rebuild_df.at[len(working_df)-1,'Close']],
                        f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [0],
                        'Candles_Missing_To_Print': [minutes_missing],
                        'Candle_Can_Be_Printed' : [False]
                        #'Volume' : [volume]
                    })

                    rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)
                    
        #LAST CANDLE MISSING
        date = lst_of_datetimes[-1]
        working_df = df_m1[df_m1['Date'] >= date]
        open = working_df.at[(len(df_m1) - len(working_df)),'Open']
        high = max(working_df['High'])
        low = min(working_df['Low'])
        close = working_df.at[len(df_m1)-1,'Close']

        #GET WHAT 'minutes' ARE MISSING
        minutes = 0 
        minutes_missing = []
        while minutes < timeframe_mult:

            if working_df['Date'].eq(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes)).any() == False: #SPECIFIC MINUTES DO NOT EXIST

                minutes_missing.append(lst_of_datetimes[ind-1]+datetime.timedelta(minutes=minutes))
                minutes += 1

            else: #SPECIFIC MINUTE EXISTS

                minutes += 1

        df_to_concat = pd.DataFrame(data={
            'Date': [date if timeframe_mult < 24*60 else date + datetime.timedelta(days=1)],
            'Candles_Transformation' : [f'M{timeframe_mult}'],
            'Open': [open],
            'High': [high],
            'Low': [low],
            'Close' : [close],
            f'M1_Candles_Used_To_Print_M{timeframe_mult}_Candle' : [len(working_df)],
            'Candles_Missing_To_Print': [minutes_missing],
            'Candle_Can_Be_Printed' : [False if len(working_df) == 0 else True]
            #'Volume' : [volume]
        })

        rebuild_df = pd.concat([rebuild_df,df_to_concat],ignore_index = True)

        return rebuild_df

