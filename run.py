#%%
import datetime
import MetaTrader5 as mt5
import pytz

#%%

from data_preparation_mt5.data_load.data_loader import ensure_sunday_date,mt5_import_to_df

#%%

from helpers import helpers_funcs
from helpers.backtest_classes import *
from strategies import strat_1

#%%

"DATA COLLECTION"

symbol = "EURUSD"
tf_m1 = mt5.TIMEFRAME_M1
tz = pytz.timezone("America/New_York")
tz_utc = pytz.UTC
start_date = ensure_sunday_date(datetime(year=2012,month=4,day=1,tzinfo=tz_utc)) #month 4 and day 1
end_date = ensure_sunday_date(datetime(year=2012,month=6,day=24,tzinfo=tz_utc))

df_m1 = mt5_import_to_df(symbol,tf_m1,start_date,end_date)


#%%

candles = [
    Candle(
        timestamp = row.Date.to_pydatetime(),
        open = row.Open,
        high = row.High,
        low = row.Low,
        close = row.Close,
        tick_volume = row.Tick_Volume
    ) for row in df_m1.itertuples()
]

#%%

portfolio = Portfolio(
    active_positions = [],
    closed_trades = [],
    disposable_balance = 100.0,
    lst_disposable_balance = [],
    unrealized_balance = 100.0,
    lst_unrealized_balance = [],
    equity_curve = 100.0,
    lst_equity_curve = [],
    lst_pct_drawdown = []
)

broker = BrokerSimulator(
    instrument = [],
    portfolio = portfolio
)

n_timeframes = helpers_funcs.number_timeframes_used()
timeframes_used = helpers_funcs.timeframes_chosen(n_timeframes)
lst_tf_strat_signal = list()
lst_tf_engines = list()

#STRAT BUILDOUT USING MULTIPLE TIMEFRAMES.


for i in range(len(timeframes_used)):

    #TAKE OUT THE QUOTATION MARKS WHENEVER YOU DONE BUILDING EACH TF ENGINE
    n_tf = i + 1

    current_tf = list(timeframes_used.keys())[i]

    if n_tf == 1:

        m1_behavior = strat_1.M1_Strat_Signal()

        lst_tf_strat_signal.append(m1_behavior)

        m1_Engine = Engine(
            indicators = {
                'sma_slow' : SMA(length_sma = strat_1.m1_slow_sma_length,role="slow"),
                'sma_fast' : SMA(length_sma = strat_1.m1_fast_sma_length,role="fast")
            },
            structure = Structure(strat_1.m1_front_back_candles_structure),
            strat_signal = lst_tf_strat_signal[i]
        )

        lst_tf_engines.append(m1_Engine)

    elif n_tf == 2:
    
        m5_behavior = strat_1.M5_Strat_Signal()
                    
        lst_tf_strat_signal.append(m5_behavior)

        m5_Engine = Engine(
            indicators = {
                'rsi' : RSI(period_size_gains_losses = strat_1.m5_rsi_size_measurement_period,role="rsi")
            },
            structure = Structure(strat_1.m5_front_back_candles_structure),
            strat_signal = lst_tf_strat_signal[i]
        )

        lst_tf_engines.append(m5_Engine)

    elif n_tf == 3:

        m15_behavior = strat_1.M15_Strat_Signal()
    
        lst_tf_strat_signal.append(m15_behavior)

        m15_Engine = Engine(
            indicators = {
                'rsi' : RSI(period_size_gains_losses = strat_1.m15_rsi_size_measurement_period,role="rsi"),
                'sma_slow' : SMA(length_sma = strat_1.m15_slow_sma_length,role="slow"),
                'sma_fast' : SMA(length_sma = strat_1.m15_fast_sma_length,role="fast") 
            },
            structure = Structure(strat_1.m15_front_back_candles_structure),
            strat_signal = lst_tf_strat_signal[i]
        )

        lst_tf_engines.append(m15_Engine)


    #IF YOU DON'T USE 4 TFS, MANUALLY REMOVE LATER TFs TILL 'n_tf' == 'timeframes'

dic_engines = helpers_funcs.dict_all_engines(lst_tf_engines,timeframes_used)
buffers = helpers_funcs.dict_buffers(timeframes_used)
timeframes = helpers_funcs.dict_timeframes(timeframes_used)
latest_htf_candle = helpers_funcs.dict_next_opens(timeframes_used)
next_opens = helpers_funcs.dict_next_opens(timeframes_used)
latest_setups = helpers_funcs.latest_setup(timeframes_used)
strucs_when_trade = helpers_funcs.struct_when_trade(timeframes_used)

multi_tf_engine = MultiTimeframeEngine(
    engines = dic_engines,
    buffers = buffers,
    timeframes = timeframes,
    last_htf_candle= latest_htf_candle,
    next_expected_open = next_opens,
    latest_setups = latest_setups,
    structures_when_trade_is_entered = strucs_when_trade,
)


exec_machine = ExecutionEngine(
    multi_tf_engine = multi_tf_engine,
    broker = broker
)


backtest = BacktestRunner()

#%%

backtest = BacktestRunner.run_backtest(backtest,execution_machine = exec_machine,lst_hist_candles = candles)



