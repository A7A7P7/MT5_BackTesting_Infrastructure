#%%


"""

STRATEGY DESCRIPTION:

TFs Used : M1,M5,M15

- ONLY BUY STRATEGY

CONDITIONS TO ENTRY:

- M1 : Fast_SMA Crossing Above Slow_SMA both at M1

- M5 : RSI(14) < Given Value

- M15 : Fast_SMA Crossing Above Slow_SMA both at M15 & RSI < Given Value

TP AND SL CONDITIONS:

SL:

    - Based on Structure which is a component of each TF, pick Local Highs or Lows for SL
    - For FX, currently only thing available, Pips on SL define the minimum pips for TP

TP:

    - Minimum pips for TP is, at least, the pips, of SL making, at least, 1:1 Risk_To_Reward
    - TP is also dependent on Local Highs or Local Lows,

"""


#%%

from datetime import datetime
from dataclasses import dataclass

#%%

"""INPUTS FOR STRATEGY"""

#M1

m1_slow_sma_length = int(input("Length Slow SMA in M1: "))
m1_fast_sma_length = int(input("Length Fast SMA in M1: "))
m1_front_back_candles_structure = int(input("Nª of Candles for LookBACK & LookFORWARD to test Local Highs & Local Lows in M1: "))

#M5

m5_rsi_size_measurement_period = int(input("Measurement Period for RSI in M5: "))
m5_front_back_candles_structure = int(input("Nª of Candles for LookBACK & LookFORWARD to test Local Highs & Local Lows in M5: "))

#M15

m15_rsi_size_measurement_period = int(input("Measurement Period for RSI in M15: "))
m15_slow_sma_length = int(input("Length Slow SMA in M15: "))
m15_fast_sma_length = int(input("Length Fast SMA in M15: "))
m15_front_back_candles_structure = int(input("Nª of Candles for LookBACK & LookFORWARD to test Local Highs & Local Lows in M15: "))

#%%

"""CLASS USED TO STORED AT EACH POINT IN TIME WHAT IS OCCURRING IN TERMS OF STRATEGY"""

@dataclass
class StrategyContext:

    indicator_values : dict
    structure_snapshot : dict
    structure_events : list
    timestamp : datetime
    #timeframe
    #htf_context
    #ltf_context
    #session_state
    #position_state

    def clean_list(self):

        self.structure_events.clear()

    def clean_dict(self):

        self.indicator_values.clear()
        self.structure_snapshot.clear()

#%%

"""CLASS USED TO SEND THE SIGNAL OF BUY OR SELL IF INDICATORS MEET THE SPECIFIED LEVELS"""

@dataclass
class SetupEvent:

    timeframe: str
    direction: str
    timestamp: datetime

#%%

"""CLASS CHARACTERIZING THE NEEDED BEHAVIOR IN M1 FOR THIS PARTICULAR STRATEGY"""

class M1_Strat_Signal: #NO INIT NO MEMORY, PURE STATELESS DOESN'T HAVE ANY PROPERTIES, IT DEPENDS ON PROPERTIES YOU GIVE TO YOUR INDICATORS
    
    def signal_generation(self,context:StrategyContext):
    
        timeframe_signal = 'm1'

        #Outputs From Each Indicator on Engine Class 
        all_roles = list(context.indicator_values.keys())
        sma_slow = context.indicator_values[all_roles[0]]
        sma_fast = context.indicator_values[all_roles[1]]

        #Current Timestamp of the signal
        timestamp = context.timestamp

        cond_1 = sma_slow != None
        cond_2 = sma_fast != None
        combined_comb = cond_1 and cond_2 and sma_fast > sma_slow

        if combined_comb:
        
            setup_event = SetupEvent(
                timeframe = timeframe_signal,
                direction = "BUY", #OR "SELL"
                timestamp = timestamp
            )
            return setup_event
        
        else:
        
            return None

#%%

"""CLASS CHARACTERIZING THE NEEDED BEHAVIOR IN M5 FOR THIS PARTICULAR STRATEGY"""

class M5_Strat_Signal: #NO INIT NO MEMORY, PURE STATELESS DOESN'T HAVE ANY PROPERTIES, IT DEPENDS ON PROPERTIES YOU GIVE TO YOUR INDICATORS

    def signal_generation(self,context:StrategyContext):
    
        timeframe_signal = 'm5'

        #Outputs From Each Indicator on Engine Class 
        all_roles = list(context.indicator_values.keys())
        rsi = context.indicator_values[all_roles[0]]

        #Current Timestamp of the signal
        timestamp = context.timestamp

        #If useful, use Current Structure Direction of that Timeframe
        direction = context.structure_snapshot['active_range'].direction #DROP IF YOU DON'T WANT TO USE IT IN A SPECIFIC TF
        
        cond_1 = rsi != None 
        combined_comb = cond_1 and rsi < 25

        if combined_comb:
        
            setup_event = SetupEvent(
                timeframe = timeframe_signal,
                direction = "BUY", #OR "SELL"
                timestamp = timestamp
            )
            return setup_event
        
        else:
        
            return None
        
#%%

"""CLASS CHARACTERIZING THE NEEDED BEHAVIOR IN M15 FOR THIS PARTICULAR STRATEGY"""

class M15_Strat_Signal: #NO INIT NO MEMORY, PURE STATELESS DOESN'T HAVE ANY PROPERTIES, IT DEPENDS ON PROPERTIES YOU GIVE TO YOUR INDICATORS 

    def signal_generation(self,context:StrategyContext):
    
        timeframe_signal = 'm15'

        #Outputs From Each Indicator on Engine Class 
        all_roles = list(context.indicator_values.keys())
        rsi = context.indicator_values[all_roles[0]]
        sma_slow = context.indicator_values[all_roles[1]]
        sma_fast = context.indicator_values[all_roles[2]]

        #Current Timestamp of the signal
        timestamp = context.timestamp

        #If useful, use Current Structure Direction of that Timeframe
        direction = context.structure_snapshot['active_range'].direction #DROP IF YOU DON'T WANT TO USE IT IN A SPECIFIC TF
        cond_direction = direction == "Low-High"

        cond_1 = rsi != None and rsi < 30
        cond_2 = sma_slow != None
        cond_3 = sma_fast != None
        combined_comb = cond_direction and cond_1 and cond_2 and cond_3 and sma_fast > sma_slow

        if combined_comb:
        
            setup_event = SetupEvent(
                timeframe = timeframe_signal,
                direction = "BUY", #OR "SELL"
                timestamp = timestamp
            )
            return setup_event
        
        else:
        
            return None