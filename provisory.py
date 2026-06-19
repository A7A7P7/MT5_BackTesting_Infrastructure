#%%

import pandas as pd
import numpy as np
import time
import datetime
import MetaTrader5 as mt5
import pytz

#%%

from data_preparation_mt5.data_clean.data_cleaner import df_m1_cleaning
from data_preparation_mt5.data_inspect.data_inspection_tfs_adjustments import different_timeframe,missing_candles_m1_ny_time
from data_preparation_mt5.data_load.data_loader import ensure_sunday_date,mt5_import_to_df
from data_preparation_mt5.data_store_fetch_cache.data_store_fetch_cache import store_in_parquet_m1_dataset,read_parquet_to_df
from data_preparation_mt5.collect_df_data_to_use import df_m1_for_test

#%%

df_to_work = df_m1_for_test

#%%

df_eurusd_m1 = read_parquet_to_df(r"C:\Users\Afons\Investments\Caching_mt5_fx_pairs_m1","EURUSD")

#%%

#START_DATE TO FETCH
year_start = int(input('Initial year to fetch from: '))
month_start = int(input('Initial month to fetch from: '))
day_start = int(input('Initial day to fetch from: '))

start = datetime.datetime(year_start, month_start, day_start)

#USE FUNCTION OF 'data_loader' TO CHECK IF IT IS SUNDAY

start = ensure_sunday_date(start)

def get_m1_symbol_data(symbol,start_date:datetime.datetime) -> pd.DataFrame: #GET DF M1 OF A SYMBOL SINCE START DATE

    tz_utc = pytz.UTC
    batch_end_date = datetime.datetime(year=start_date.year+1,month=3,day=9,tzinfo=tz_utc)
    current_year = datetime.date.today().year
    all_years_df_m1 = pd.DataFrame()

    while batch_end_date.year <= current_year:

        df_m1 = mt5_import_to_df(symbol,tf_m1,start_date,batch_end_date)
        df_m1 = df_m1_cleaning(df_m1)
        dic_stats_df = missing_candles_m1_ny_time(df_m1)
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

all_years_df_m1 = get_m1_symbol_data("EURUSD",start)

dic_stats_df = missing_candles_m1_ny_time(all_years_df_m1)

data_missing_candles = dic_stats_df["data_missing_candles"]

df_m1 = dic_stats_df['df_m1']

#%%

symbol = "EURUSD"
tf_m1 = mt5.TIMEFRAME_M1
tz = pytz.timezone("America/New_York") #
tz_utc = pytz.UTC
start_date_fetch = datetime.datetime(year=2012,month=3,day=9,tzinfo=tz_utc)
batch_end_date = datetime.datetime(year=start_date_fetch.year+1,month=3,day=9,tzinfo=tz_utc)
current_year = datetime.date.today().year
all_years_df_m1 = pd.DataFrame()

while batch_end_date.year <= current_year:

    df_m1 = mt5_import_to_df(symbol,tf_m1,start_date_fetch,batch_end_date)
    df_m1 = df_m1_cleaning(df_m1)
    dic_stats_df = missing_candles_m1_ny_time(df_m1)
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
    
    start_date_fetch = batch_end_date
    batch_end_date = datetime.datetime(year=start_date_fetch.year+1,month=3,day=9,tzinfo=tz_utc)
    while batch_end_date.weekday() != 6:

        batch_end_date_ordinal = batch_end_date.toordinal()
        batch_end_date_ordinal_test = batch_end_date_ordinal - 1
        batch_end_date = datetime.datetime.fromordinal(batch_end_date_ordinal_test)
    
    print(len(all_years_df_m1),start_date_fetch,batch_end_date)

#%%

all_years_df_m1

dic_stats_df = missing_candles_m1_ny_time(all_years_df_m1)

data_missing_candles = dic_stats_df["data_missing_candles"]

df_m1 = dic_stats_df['df_m1']

#%%

y25_26_m1


#%%

conditions = (
    (pd.to_datetime(all_years_df_m1["Day&Datetime"]).dt.day < 10) & (pd.to_datetime(all_years_df_m1["Day&Datetime"]).dt.month == 3)
)

all_years_df_m1[conditions].reset_index(drop=True)[1100:1200]

#%%

all_years_df_m1 = pd.DataFrame()
len(all_years_df_m1)



#%%

symbol = "EURUSD"
tf_m1 = mt5.TIMEFRAME_M1
tz = pytz.timezone("America/New_York") #
tz_utc = pytz.UTC
start_date = ensure_sunday_date(datetime.datetime(year=2012,month=3,day=4,tzinfo=tz_utc))
end_date = ensure_sunday_date(datetime.datetime(year=2013,month=3,day=3,tzinfo=tz_utc))

df_m1 = mt5_import_to_df(symbol,tf_m1,start_date,end_date)

#%%

df_m1

#%%

df_m1 = df_m1_cleaning(df_m1)

dic_stats_df = missing_candles_m1_ny_time(df_m1)

data_missing_candles = dic_stats_df["data_missing_candles"]

df_m1 = dic_stats_df['df_m1']

"""374400 possible rows were found 371134 rows
    which is 99% of all the data
   374400-371134 = 3266
   3266 / 1440 = 2.26 proxy, so basically in candles lost, one lost 2 days and a quarter of data
"""
#%%

y24_25_m1 = df_m1
y24_25_m1

#%%
y25_26_m1

#%%
all_years_df_m1


#%%

df_m5 = different_timeframe(df_m1,5)

df_m15 = different_timeframe(df_m1,15)

#%%

y25_26_m1 = df_m1
y25_26_m5 = df_m5
y25_26_m15 = df_m15

#%%



#%%

df_m5[df_m5["Candle_Can_Be_Printed"] == False]

len(df_m15[df_m15["M1_Candles_Used_To_Print_M15_Candle"] <= 10])


#%%

days_with_missing_info = [l[0] for l in data_missing_candles]

days_with_missing_info

#%%


#%%

datetime.datetime(year=2012,month=10,day=8,tzinfo=tz_utc).weekday()

#%%
rates_frame = pd.DataFrame(rates)
# convert time in seconds into the datetime format
rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
rates_frame["time"] = rates_frame["time"] - pd.Timedelta(hours=2) - pd.Timedelta(hours=5) #FIRST 2 TO ADJUST THE OPENING, NEXT 5 TO PUT NY TIME

#%%

rates_frame.loc[990:1030,:]
rates_frame

#%%

rates_frame.loc[21560:21610,:]

#%%

rates_frame.loc[21430+1440*5:21480+1440*5,:]


#%%

if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

#%%
#INITIALIZATION

#Connecting data to metatrader5

mt5.initialize(path = r"C:\Users\Afons\mt5setup.exe")

#%%

#LOGIN

my_account = mt5.login(  
    login=52888011, 
    server="ICMarketsEU-Demo",
    password="V$6iwqov58RttH")

#%%

my_account


# %%

#%%
# %%


def daily_historical_returns(df,first_day_trade):

    daily_returns = [ret for ret in df.loc[first_day_trade:,'Returns']]

    return daily_returns

def n_paths(daily_r = daily_historical_returns(equity_df,l_days_trades[0])): #return total_balance_paths,avg_path and median path

    np.random.seed(1) #Just to make sure that permutations won't change if things are run again. However, if input for permutations change, permutations will change regardless of seed

    lst_of_paths = [np.random.permutation(daily_r) for path_n in range(n_sims)]
    total_balance_paths = []
    final_above_initial = 0

    for n_sim in range(n_sims):

        return_path = lst_of_paths[n_sim]
        total_balance_path = [initial_capital]

        for ret in return_path:

            total_balance_path.append(total_balance_path[-1]*(1+ret))
        
        total_balance_paths.append(total_balance_path)
        final_above_initial +=1 if total_balance_path[-1] > initial_capital else 0

    #Average points at each day of all the paths
    avg_path = np.mean(total_balance_paths, axis=0)

    #Median point at each day of all the paths
    median_path = np.median(total_balance_paths, axis=0)

    return [total_balance_paths,avg_path,median_path,final_above_initial]

def Monte_Carlo_graph_permutation(type = matplotlib_plotly, paths = n_paths(daily_r = daily_historical_returns(equity_df,l_days_trades[0]))):

    if type == 'plotly' or type == 'matplotlib':

        if type == 'plotly':

            #Create figure
            fig = go.Figure()

            """
            # Optional: 5th and 95th percentile bands
            lower_percentile = np.percentile(paths[0], 5, axis=0)
            upper_percentile = np.percentile(paths[0], 95, axis=0)
            """

            # X-axis (days)
            days = np.arange(len(paths[0][0])) #create a array from 0 to the input

            # array_initial_capital

            init_capital_path = np.array([initial_capital for n in range(len(paths[0][0]))])

            # Create the figure
            fig = go.Figure()

            # 1. Plot all simulation paths (transparent)
            for path in paths[0]:
                fig.add_trace(go.Scatter(
                    x=days, y=path,
                    mode='lines',
                    line=dict(color='blue', width=1),
                    opacity=0.1,
                    showlegend=False
                ))

            # 2. Plot mean path
            fig.add_trace(go.Scatter(
                x=days, y=paths[1],
                mode='lines',
                line=dict(color='green', width=3, dash='dash'),
                name='Mean Path'
            ))

            # 3. Plot median path
            fig.add_trace(go.Scatter(
                x=days, y=paths[2],
                mode='lines',
                line=dict(color='red', width=3),
                name='Median Path'
            ))

            # 4. Plot initial_capital line
            fig.add_trace(go.Scatter(
                x=days, y=init_capital_path,
                mode='lines',
                line=dict(color='white', width=3),
                name='Initial_Capital_Line'
            ))
            """
            # 4. Add 5–95% percentile band
            fig.add_trace(go.Scatter(
                x=np.concatenate([days, days[::-1]]),
                y=np.concatenate([upper_percentile, lower_percentile[::-1]]),
                fill='toself',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='5–95% Band'
            ))
            """
            # Update layout
            fig.update_layout(
                title='Monte Carlo Simulation of Portfolio',
                xaxis_title='Days',
                yaxis_title='Portfolio Value',
                template='plotly_dark',
                #paper_bgcolor='white',  # background around the plot, overrides template colors
                #plot_bgcolor='lightgray',  # background inside the plot area, overrides template colors
                width = 2500,
                height = 900
            )

            return fig.show()

        else: #'matplotlib'
            
            plt.figure(figsize=(30,10))
            for path in paths[0]: # alpha is to avoid very dark lines for them to not overlap each other
                plt.plot(path,alpha=0.35, lw = 0.7 )
            plt.plot(paths[1], color = 'blue',alpha = 1, linewidth = 5, ls = 'dashed',) #ls is linestyle and default is 'solid'
            plt.plot(paths[2], color = 'red',alpha = 1, linewidth = 5, ls = 'dotted') #ls is linestyle and default is 'solid'
            plt.axhline(initial_capital, color = 'black')
            plt.annotate(text=f'{paths[3]/n_sims*100} % - Pct of times where final capital > above initial' , xy= [0,0])
            return plt.show()
        
    else: #Neither Matplotlib nor plotly

        return 'Re-run and choose right type of graph'



#Monte_Carlo_graph_permutation()

# %% [markdown]
#                                                                                         MONTE-CARLO BASED ON DIFFERENT PATHS NOT PERMUTATIONS WITH ENDING VALUES, HOPEFULLY DIFFERING AND MORE RETURNS CLUSTERING

# %%
matplotlib_plotly = str(input('Type of graph: plotly or matplotlib (write on off the 2)')).lower()

def daily_historical_returns(df,first_day_trade):

    daily_returns = [ret for ret in df.loc[first_day_trade:,'Returns']]

    return daily_returns

def n_total_balance_paths(n_simulations = n_sims,days_of_persistence = duration_persistence_in_days, returns_distribution = equity_df['Returns']): #return total_balance_paths,avg_path and median path

    returns_paths = all_return_paths(n_simulations,days_of_persistence,returns_distribution) #lst_paths and np.random.seed already included in here

    total_balance_paths = []
    final_above_initial = 0

    for n_sim in range(n_simulations):

        return_path = returns_paths[n_sim]
        total_balance_path = [initial_capital]

        for ret in return_path:

            total_balance_path.append(total_balance_path[-1]*(1+ret))
        
        total_balance_paths.append(total_balance_path)
        final_above_initial +=1 if total_balance_path[-1] > initial_capital else 0

    #Average points at each day of all the paths
    avg_path = np.mean(total_balance_paths, axis=0)

    #Median point at each day of all the paths
    median_path = np.median(total_balance_paths, axis=0)

    return [total_balance_paths,avg_path,median_path,final_above_initial]

def Monte_Carlo_graph_no_permutation(type = matplotlib_plotly, paths = n_total_balance_paths(n_sims,duration_persistence_in_days,equity_df['Returns'])):

    if type == 'plotly' or type == 'matplotlib':

        if type == 'plotly':

            #Create figure
            fig = go.Figure()

            """
            # Optional: 5th and 95th percentile bands
            lower_percentile = np.percentile(paths[0], 5, axis=0)
            upper_percentile = np.percentile(paths[0], 95, axis=0)
            """

            # X-axis (days)
            days = np.arange(len(paths[0][0])) #create a array from 0 to the input

            # array_initial_capital

            init_capital_path = np.array([initial_capital for n in range(len(paths[0][0]))])

            # Create the figure
            fig = go.Figure()

            # 1. Plot all simulation paths (transparent)
            for path in paths[0]:
                fig.add_trace(go.Scatter(
                    x=days, y=path,
                    mode='lines',
                    line=dict(color='blue', width=1),
                    opacity=0.1,
                    showlegend=False
                ))

            # 2. Plot mean path
            fig.add_trace(go.Scatter(
                x=days, y=paths[1],
                mode='lines',
                line=dict(color='green', width=3, dash='dash'),
                name='Mean Path'
            ))

            # 3. Plot median path
            fig.add_trace(go.Scatter(
                x=days, y=paths[2],
                mode='lines',
                line=dict(color='red', width=3),
                name='Median Path'
            ))

            # 4. Plot initial_capital line
            fig.add_trace(go.Scatter(
                x=days, y=init_capital_path,
                mode='lines',
                line=dict(color='white', width=3),
                name='Initial_Capital_Line'
            ))
            """
            # 4. Add 5–95% percentile band
            fig.add_trace(go.Scatter(
                x=np.concatenate([days, days[::-1]]),
                y=np.concatenate([upper_percentile, lower_percentile[::-1]]),
                fill='toself',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='5–95% Band'
            ))
            """
            # Update layout
            fig.update_layout(
                title='Monte Carlo Simulation of Portfolio',
                xaxis_title='Days',
                yaxis_title='Portfolio Value',
                template='plotly_dark',
                #paper_bgcolor='white',  # background around the plot, overrides template colors
                #plot_bgcolor='lightgray',  # background inside the plot area, overrides template colors
                width = 2500,
                height = 900
            )

            return fig.show()

        else: #'matplotlib'
            
            plt.figure(figsize=(30,10))
            for path in paths[0]: # alpha is to avoid very dark lines for them to not overlap each other
                plt.plot(path,alpha=0.35, lw = 0.7 )
            plt.plot(paths[1], color = 'blue',alpha = 1, linewidth = 5, ls = 'dashed',) #ls is linestyle and default is 'solid'
            plt.plot(paths[2], color = 'red',alpha = 1, linewidth = 5, ls = 'dotted') #ls is linestyle and default is 'solid'
            plt.axhline(initial_capital, color = 'black')
            plt.annotate(text=f'{paths[3]/n_sims*100} % - Pct of times where final capital > above initial' , xy= [0,0])
            return plt.show()
        
    else: #Neither Matplotlib nor plotly

        return 'Re-run and choose right type of graph'