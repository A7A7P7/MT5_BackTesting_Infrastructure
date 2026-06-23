#%%

import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from collections import deque
from copy import deepcopy
import math
import plotly.graph_objects as go

#%%

#CANDLES TREATMENT

@dataclass
class Candle:
        
    timestamp: datetime

    open: float
    high: float
    low: float
    close: float

    tick_volume: float = 0

#STRUCTURE AND RANGES

@dataclass
class RangeState:

    high: float
    low: float
    timestamp_high: datetime
    timestamp_low: datetime
    direction: str

    def set_range_after_updating_direction(self,high:float,low:float,ts_high:datetime,ts_low:datetime):

        self.high = high
        self.low = low
        self.timestamp_high = ts_high
        self.timestamp_low = ts_low
    
    def set_low_when_direction_changes(self,low:float,ts_low:datetime,direction="High-Low"):

        self.direction = direction
        self.low = low
        self.timestamp_low = ts_low
    
    def set_low_when_direction_maintains(self,low:float,ts_low:datetime):

        self.low = low
        self.timestamp_low = ts_low 

    def set_high_when_direction_changes(self,high:float,ts_high:datetime,direction="Low-High"):

        self.direction = direction
        self.high = high
        self.timestamp_high = ts_high

    def set_high_when_direction_maintains(self,high:float,ts_high:datetime):

        self.high = high
        self.timestamp_high = ts_high

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

class Structure:

    def __init__(self,back_front_n_candles_for_extremes:int):

        #Only variable needed to iniatilize the Structure Class
        self.back_front_n_candles_for_extremes = back_front_n_candles_for_extremes

        self.window_highs_lows = deque(maxlen=((self.back_front_n_candles_for_extremes*2)+1))

        self.lst_local_highs = list()
        self.lst_local_highs_ts = list() 
        self.lst_local_lows = list()
        self.lst_local_lows_ts = list()

        self.active_range = RangeState(
            high = None,
            low = None,
            timestamp_high = None,
            timestamp_low = None,
            direction = None
        )

        self.prev_range = RangeState(
            high = None,
            low = None,
            timestamp_high = None,
            timestamp_low = None,
            direction = None
        )

        self.ready = False

        self.events = []
        self.dict_time_fvg = {}
        self.candles_in_range = []
        self.premium = None
        self.discount = None
        

    def local_lows_highs_and_timestamps(self):

        idx_to_inspect = self.back_front_n_candles_for_extremes
        candle_to_inspect = self.window_highs_lows[idx_to_inspect]
        window_high = max(c.high for c in self.window_highs_lows)
        window_low = min(c.low for c in self.window_highs_lows)
        value_is_local_high = candle_to_inspect.high >= window_high
        value_is_local_low = candle_to_inspect.low <= window_low

        if value_is_local_high or value_is_local_low: #NEW CANDLE IS EITHER A LOCAL HIGH OR A LOCAL LOW

            if value_is_local_high and value_is_local_low: #NEW CANDLE IS BOTH A HIGH AND A LOW

                self.lst_local_highs.append(candle_to_inspect.high)
                self.lst_local_highs_ts.append(candle_to_inspect.timestamp)
                self.lst_local_lows.append(candle_to_inspect.low)
                self.lst_local_lows_ts.append(candle_to_inspect.timestamp)

                occurrence = {
                    'category' : 'local_extremes',
                    'type' : 'NEW_LOCAL_HIGH',
                    'timestamp' : candle_to_inspect.timestamp,
                    'price' : candle_to_inspect.high
                }

                self.events.append(occurrence)

                occurrence = {
                    'category' : 'local_extremes',
                    'type' : 'NEW_LOCAL_LOW',
                    'timestamp' : candle_to_inspect.timestamp,
                    'price' : candle_to_inspect.low
                }

                self.events.append(occurrence)

            else: # ~value_is_local_high or ~value_is_local_low , NEW candle_to_inspect ONLY HIGH OR LOW

                if value_is_local_low == False: #NEW candle_to_inspect IS A HIGH

                    self.lst_local_highs.append(candle_to_inspect.high)
                    self.lst_local_highs_ts.append(candle_to_inspect.timestamp)

                    occurrence = {
                        'category' : 'local_extremes',
                        'type' : 'NEW_LOCAL_HIGH',
                        'timestamp' : candle_to_inspect.timestamp,
                        'price' : candle_to_inspect.high
                    }

                    self.events.append(occurrence)
                
                else: #NEW candle_to_inspect IS A LOW

                    self.lst_local_lows.append(candle_to_inspect.low)
                    self.lst_local_lows_ts.append(candle_to_inspect.timestamp)

                    occurrence = {
                        'category' : 'local_extremes',
                        'type' : 'NEW_LOCAL_LOW',
                        'timestamp' : candle_to_inspect.timestamp,
                        'price' : candle_to_inspect.low
                    }

                    self.events.append(occurrence)


    def new_range_when_direction_changes(self,new_high_or_low:float,new_ts_high_or_low:datetime,new_dir:str):

        prev_dir = self.active_range.direction

        if prev_dir == "Low-High":

            """RANGE CHANGES TO 'High-Low'"""

            self.active_range.set_low_when_direction_changes(new_high_or_low,new_ts_high_or_low,new_dir)

            #ADJUSTMENT OF THE HIGH
            copy_candles_in_range = self.candles_in_range.copy()
            lst_ts_candles_in_range = [c.timestamp for c in copy_candles_in_range]

            idx_last_extreme_prev_range = lst_ts_candles_in_range.index(self.prev_range.timestamp_high)
            lst_range_of_interest = copy_candles_in_range[idx_last_extreme_prev_range:]
            lst_highs = [c.high for c in lst_range_of_interest]
            lst_ts = [c.timestamp for c in lst_range_of_interest]
            lst_highs.reverse() #index method of list turns the 1st index, so I need to reverse, just in case of equality of highs, it turns the most recent
            lst_ts.reverse() #index method of list turns the 1st index, so I need to reverse, just in case of equality of highs, it turns the most recent
            new_high = max(lst_highs)
            idx_high = lst_highs.index(new_high)
            ts_high = lst_ts[idx_high]

            self.active_range.high = new_high
            self.active_range.timestamp_high = ts_high


        else: #"High-Low"

            """RANGE CHANGES TO 'Low-High'"""

            self.active_range.set_high_when_direction_changes(new_high_or_low,new_ts_high_or_low,new_dir)

            #ADJUSTMENT OF THE LOW
            copy_candles_in_range = self.candles_in_range.copy()
            lst_ts_candles_in_range = [c.timestamp for c in copy_candles_in_range]

            idx_last_extreme_prev_range = lst_ts_candles_in_range.index(self.prev_range.timestamp_low)
            lst_range_of_interest = copy_candles_in_range[idx_last_extreme_prev_range:]
            lst_lows = [c.low for c in lst_range_of_interest]
            lst_ts = [c.timestamp for c in lst_range_of_interest]
            lst_lows.reverse() #index method of list turns the 1st index, so I need to reverse, just in case of equality of lows, it turns the most recent
            lst_ts.reverse() #index method of list turns the 1st index, so I need to reverse, just in case of equality of lows, it turns the most recent
            new_low = min(lst_lows)
            idx_low = lst_lows.index(new_low)
            ts_low = lst_ts[idx_low]

            self.active_range.low = new_low
            self.active_range.timestamp_low = ts_low


    def range_low_adjust_to_local_low(self,current_high_above_range_high:bool):

        #SEE IF YOU CAN UPDATE THE LOW TO A HIGHER LOCAL LOW
        dict_possible_lows = {'lows' : [], 'lows_timestamps' : []}
        for idx_low, low in enumerate(self.lst_local_lows):

            if low >= self.active_range.low:

                dict_possible_lows['lows'].append(low)
                dict_possible_lows['lows_timestamps'].append(
                    self.lst_local_lows_ts[idx_low]
                )

        if len(dict_possible_lows['lows']) != 0:

            tuple_dict_keys = tuple(ind for ind in range(len(dict_possible_lows['lows'])))
            if len(tuple_dict_keys) != 0:

                possible_lows_ts = tuple(dict_possible_lows['lows_timestamps'][ind] for ind in tuple_dict_keys)
                recent_possible_lows = tuple(dict_possible_lows['lows'][idx] for idx in tuple_dict_keys if self.active_range.timestamp_high > possible_lows_ts[idx] > self.active_range.timestamp_low)
                possible_lows_ts = tuple(timestamp for timestamp in possible_lows_ts if self.active_range.timestamp_high > timestamp > self.active_range.timestamp_low)

                if len(recent_possible_lows) != 0:

                    #Choose the latest_low that happened before the high of the range
                    low_to_use_in_range = recent_possible_lows[-1] 
                    low_tstamp = possible_lows_ts[-1]
                    prev_range_low = self.active_range.low
                    self.active_range.set_low_when_direction_maintains(low_to_use_in_range,low_tstamp)
        #             if current_high_above_range_high:
        #                 print(f"NEW ABSOLUTE HIGH IN RANGE AT {self.active_range.high}, AND AN UPDATE ON A LOW TO A NEW LOCAL LOW AT {self.active_range.low} MAINTAING THE OVERALL DIRECTION {self.active_range.direction} 1")
        #             else:
        #                 print(f"THERE ARE NO NEW LOWS LOWER THAN THE RANGE, BUT THE LOW ON THE {self.active_range.direction} CHANGED UPWARDS from {prev_range_low} TO {self.active_range.low} 2")

        #         else:

        #             print(f"FEASIBLE LOCAL LOWS, BUT THEY WEREN'T MORE RECENT THAN CURRENT ACTIVE RANGE LOW, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH LOW AT {self.active_range.low} AND HIGH AT {self.active_range.high} 3")

        #     else:

        #         print(f"NO FEASIBLE LOCAL LOWS, EVEN THOUGH EXISTENT, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH LOW AT {self.active_range.low} AND HIGH AT {self.active_range.high} 4")

        # else:

        #     print(f"NO FEASIBLE LOCAL LOWS, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH LOW AT {self.active_range.low} AND HIGH AT {self.active_range.high} 6")

    def range_high_adjust_to_local_high(self,current_low_below_range_low:bool):


        dict_possible_highs = {'highs' : [], 'highs_timestamps' : []}
        for idx_high, high in enumerate(self.lst_local_highs):

            if high <= self.active_range.high:

                dict_possible_highs['highs'].append(high)
                dict_possible_highs['highs_timestamps'].append(
                    self.lst_local_highs_ts[idx_high]
                )

        if len(dict_possible_highs['highs']) != 0:

            tuple_dict_keys = tuple(ind for ind in range(len(dict_possible_highs['highs'])))
            if len(tuple_dict_keys) != 0:

                possible_highs_ts = tuple(dict_possible_highs['highs_timestamps'][ind] for ind in tuple_dict_keys)
                recent_possible_highs = tuple(dict_possible_highs['highs'][idx] for idx in tuple_dict_keys if self.active_range.timestamp_low > possible_highs_ts[idx] > self.active_range.timestamp_high)
                possible_highs_ts = tuple(timestamp for timestamp in possible_highs_ts if self.active_range.timestamp_low > timestamp > self.active_range.timestamp_high)

                if len(recent_possible_highs) != 0:

                    #Choose the latest_high that happened before the low of the range
                    high_to_use_in_range = recent_possible_highs[-1]
                    high_tstamp = possible_highs_ts[-1]
                    prev_range_high = self.active_range.high
                    self.active_range.set_high_when_direction_maintains(high_to_use_in_range,high_tstamp)
        #             if current_low_below_range_low:
        #                 print(f"NEW ABSOLUTE LOW IN RANGE AT {self.active_range.low}, AND AN UPDATE ON A HIGH TO A NEW LOCAL HIGH AT {self.active_range.high} MAINTAING THE OVERALL DIRECTION {self.active_range.direction} 9")
        #             else:
        #                 print(f"THERE ARE NO NEW HIGHS HIGHER THAN THE RANGE, BUT THE HIGH ON THE {self.active_range.direction} CHANGED DOWNWARDS from {prev_range_high} TO {self.active_range.high} 10")

        #         else:
                    
        #             print(f"FEASIBLE LOCAL HIGHS, BUT THEY WEREN'T MORE RECENT THAN CURRENT ACTIVE RANGE HIGH, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH HIGH AT {self.active_range.high} AND LOW AT {self.active_range.low} 11")
            
        #     else:

        #       print(f"NO FEASIBLE LOCAL HIGHS,EVEN THOUGH EXISTENT, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH HIGH AT {self.active_range.high} AND LOW AT {self.active_range.low} 12")  
        
        # else:
            
        #     print(f"NO FEASIBLE LOCAL HIGHS, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH HIGH AT {self.active_range.high} AND LOW AT {self.active_range.low} 13")


    def change_candles_in_range(self,timestamp_first_extreme:datetime):

        timestamps = [c.timestamp for c in self.candles_in_range]

        if timestamp_first_extreme not in timestamps:
            print("===================================")
            print("Invariant broken")
            print("Looking for:", timestamp_first_extreme)
            print("Current direction:", self.active_range.direction)
            print("Range high:", self.active_range.timestamp_high)
            print("Range low :", self.active_range.timestamp_low)

            print("\nCandles in range:")
            for c in self.candles_in_range:
                print(c.timestamp)

            raise RuntimeError("First extreme missing from candles_in_range")

        idx = timestamps.index(timestamp_first_extreme)
        self.candles_in_range = self.candles_in_range[idx:]

    def add_fair_value_gap(self,timestamp_last_extreme:datetime):

        #self.candles_in_range always change when range changes direction
        #self.fvg_in_range always change when range changes direction

        #INSTEAD OF CALCULATING IT EVERYTIME A RANGE CHANGES, MAYBE AS YOU ADD A NEW CANDLE TO ADD TO RANGE AND CALCULATE THE POSSIBLE FVGS

        #NEED TO MAKE SURE THAT THE CANDLES CALCULATING THE FVG ARE CONSECUTIVE 

        idx_candle = len(self.candles_in_range) - 1
        
        if len(self.candles_in_range) >= 3:

            timestamps = [c.timestamp for c in self.candles_in_range]

            idx_last_extreme = timestamps.index(timestamp_last_extreme)
            candles_range_fvg = self.candles_in_range[:idx_last_extreme+1].copy()

            #print(len(self.candles_range_fvg),self.active_range.direction,f"First_Extreme : {self.active_range.timestamp_low if self.active_range.direction == "Low-High" else self.active_range.timestamp_high}, Last_Extreme : {timestamp_last_extreme} & Last_Candle_In_Range_&_Current_Candle : {self.candles_range_fvg[idx_candle].timestamp}")

            candles_ranges = [abs(c.high - c.low) for c in candles_range_fvg]
            avg_range = sum(candles_ranges) / len(candles_ranges)
            minimal_range_for_fvg = avg_range + 0.5 * (max(candles_ranges) - avg_range)
            candles_choosen = []
            idx_candles = []
            for i in range(0,len(candles_range_fvg)-2):

                cond_candle = candles_range_fvg[i+1].close >= candles_range_fvg[i+1].open if self.active_range.direction == "Low-High" else candles_range_fvg[i+1].close < candles_range_fvg[i+1].open
                rng = abs(candles_range_fvg[i+1].high - candles_range_fvg[i+1].low)
                if rng > minimal_range_for_fvg and cond_candle:
                    candles_choosen.append(candles_range_fvg[i+1])
                    idx_candles.append(i+1)

            for i in range(len(candles_choosen)):

                candle = candles_choosen[i]
                idx_candle = idx_candles[i]

                total_range = abs(candle.high - candle.low)
                op_clo_range = abs(candle.close - candle.open) if self.active_range.direction == "Low-High" else abs(candle.open - candle.close)

                if (op_clo_range / total_range) >= 0.5 :

                    prev_candle = candles_range_fvg[idx_candle-1]
                    post_candle = candles_range_fvg[idx_candle+1]
                    prev_point = prev_candle.high if self.active_range.direction == "Low-High" else prev_candle.low
                    post_point = post_candle.low if self.active_range.direction == "Low-High" else post_candle.high
                    size_fvg = post_point - prev_point if self.active_range.direction == "Low-High" else prev_point - post_point
                    mid_point = prev_point + (size_fvg / 2) if self.active_range.direction == "Low-High" else prev_point - (size_fvg / 2)
                    candles_after_start_fvg = self.candles_in_range[idx_candle+1:].copy()
                    point_of_interest = min(tuple(candle.low for candle in candles_after_start_fvg)) if self.active_range.direction == "Low-High" else max(tuple(candle.high for candle in candles_after_start_fvg))
                    no_touch_mid_point = mid_point < point_of_interest if self.active_range.direction == "Low-High" else mid_point > point_of_interest
                    fvg_has_considerable_size = size_fvg > 0.6 * op_clo_range
                    if fvg_has_considerable_size and no_touch_mid_point:

                        candle_ts_fvg = candle.timestamp
                        prev_candle_ts = prev_candle.timestamp
                        post_candle_ts = post_candle.timestamp
                        fvg_ts_start_end = [prev_candle_ts,post_candle_ts]
                        fvg = [prev_point,post_point]
                        self.dict_time_fvg[candle_ts_fvg] = dict()
                        for i in range(len(fvg)):

                            self.dict_time_fvg[candle_ts_fvg][fvg_ts_start_end[i]] = fvg[i]


    def del_fair_value_gap(self,candle:Candle):

        if len(self.dict_time_fvg) != 0:

            value_to_inspect = candle.low if self.active_range.direction == "Low-High" else candle.high
            base_timestamp = self.active_range.timestamp_low if self.active_range.direction == "Low-High" else self.active_range.timestamp_high
            init_dict = self.dict_time_fvg.copy()

            for key in init_dict:

                fvg = init_dict[key]
                p1,p2 = fvg.values()
                fvg_start_point = p1
                fvg_end_point = p2
                fvg_midpoint = fvg_start_point + ((fvg_end_point - fvg_start_point)/2) if self.active_range.direction == "Low-High" else fvg_start_point - ((fvg_start_point - fvg_end_point)/2)
                fvg_touch = value_to_inspect <= fvg_midpoint if self.active_range.direction == "Low-High" else value_to_inspect >= fvg_midpoint
                if key < base_timestamp or fvg_touch:

                    del self.dict_time_fvg[key]

    def price_at_discount_or_premium(self,candle:Candle):

        range_size = abs(self.active_range.high - self.active_range.low)

        if self.active_range.direction == "Low-High":

            mid_point = self.active_range.low + range_size / 2
            self.premium = None
            if candle.close <= mid_point:

                self.discount = True
            
            else:

                self.discount = False
        
        else:

            mid_point = self.active_range.low + range_size / 2
            self.discount = None
            if candle.close >= mid_point:

                self.premium = True
            
            else:

                self.premium = False 


    def update(self,candle:Candle): #CONSTANT UPDATE OF RANGES AND VALUES TO ASSESSED AS HIGHS AND LOWS

        #print(f"id(self) = {id(self)}")
        #print(f"Before change id(active_range) = {id(self.active_range)}")

        self.candles_in_range.append(candle)

        size_max = (self.back_front_n_candles_for_extremes*2)+1

        if len(self.window_highs_lows) < size_max :

            if len(self.window_highs_lows) < size_max - 1:

                self.window_highs_lows.append(candle)

                temp_high_list = [candle.high for candle in self.window_highs_lows]
                temp_low_list = [candle.low for candle in self.window_highs_lows]
                high_list = max(temp_high_list)
                low_list = min(temp_low_list)
                timestamp_high_idx = temp_high_list.index(high_list)
                timestamp_low_idx = temp_low_list.index(low_list)
                timestamp_high = self.window_highs_lows[timestamp_high_idx].timestamp
                timestamp_low = self.window_highs_lows[timestamp_low_idx].timestamp
                high_before_low_cond = timestamp_high < timestamp_low

                active_range_all_non = (self.active_range.high is None) and (self.active_range.timestamp_high is None) and (self.active_range.low is None) and (self.active_range.timestamp_low is None) and (self.active_range.direction is None)

                if active_range_all_non: #ONLY UPDATE ACTIVE_RANGE, 1ST RANGE, NO PREV_RANGE

                    if high_before_low_cond :

                        self.active_range.direction = "High-Low"
                    
                    else:

                        self.active_range.direction = "Low-High"
                    
                    self.active_range.set_range_after_updating_direction(high_list,low_list,timestamp_high,timestamp_low)
                    #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes at {candle.timestamp}")
                
                else: #PREV_RANGE WILL EXIST

                    #UPDATE PREV_RANGE
                    self.prev_range = deepcopy(self.active_range)

                    high_changed = self.active_range.timestamp_high != timestamp_high
                    low_changed = self.active_range.timestamp_low != timestamp_low
                    one_changed = high_changed or low_changed

                    if one_changed:

                        if high_changed and low_changed: #both changes

                            if high_before_low_cond :

                                self.active_range.direction = "High-Low"
                            
                            else:

                                if timestamp_high == timestamp_low:

                                    candle_open = self.window_highs_lows[timestamp_high_idx].open
                                    candle_close = self.window_highs_lows[timestamp_high_idx].close
                                    self.active_range.direction = "High-Low" if candle_open >= candle_close else "Low-High"

                                else:

                                    self.active_range.direction = "Low-High"

                            self.active_range.set_range_after_updating_direction(high_list,low_list,timestamp_high,timestamp_low)
                            self.candles_in_range = []
                            self.candles_in_range.append(candle)
                            self.discount = False
                            self.premium = False
                            #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes at {candle.timestamp}")
                            
                        else: #~high_changed or ~low_changed

                            if high_changed == True and low_changed == False: #IT MEANS LOW DIDN'T CHANGE

                                if self.active_range.direction == "Low-High":

                                    #print(f"Prev_Active_Range , First_Extreme : {self.active_range.timestamp_low}, Last_Extreme : {self.active_range.timestamp_high}, Current_Candle : {candle.timestamp}, Before change id(active_range) = {id(self.active_range)}")
                                    self.active_range.set_high_when_direction_maintains(candle.high,candle.timestamp)
                                    #print(f"Current_Active_Range , First_Extreme : {self.active_range.timestamp_low}, Last_Extreme : {self.active_range.timestamp_high}, Current_Candle : {candle.timestamp}, After change id(active_range) = {id(self.active_range)}")
                                    self.add_fair_value_gap(timestamp_high)
                                    self.del_fair_value_gap(candle)
                                    self.price_at_discount_or_premium(candle)
                                    #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH SAME DIRECTION Low-High at {candle.timestamp}")
                                
                                else: #High-Low

                                    self.new_range_when_direction_changes(candle.high,candle.timestamp,"Low-High")
                                    #self.active_range.set_high_when_direction_changes(candle.high,candle.timestamp,"Low-High")
                                    self.change_candles_in_range(self.active_range.timestamp_low)
                                    self.add_fair_value_gap(self.active_range.timestamp_high)
                                    self.del_fair_value_gap(candle)
                                    self.price_at_discount_or_premium(candle)
                                    #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH SAME DIRECTION CHANGING TO Low-High at {candle.timestamp}")

                                    occurrence = {
                                        'category' : 'range',
                                        'type' : 'RANGE_DIRECTION_CHANGED_TO_LOW-HIGH',
                                        'timestamp' : candle.timestamp,
                                        'price' : candle.high
                                    }

                                    self.events.append(occurrence)
                            
                            elif high_changed == False and low_changed == True: #IT MEANS LOW CHANGED AND HIGH DIDN'T

                                if self.active_range.direction == "Low-High":

                                    self.new_range_when_direction_changes(candle.low,candle.timestamp,"High-Low")
                                    #self.active_range.set_low_when_direction_changes(candle.low,candle.timestamp,"High-Low")
                                    self.change_candles_in_range(self.active_range.timestamp_high)
                                    self.add_fair_value_gap(self.active_range.timestamp_low)
                                    self.del_fair_value_gap(candle)
                                    self.price_at_discount_or_premium(candle)
                                    #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH SAME DIRECTION CHANGING TO High-Low at {candle.timestamp}")

                                    occurrence = {
                                        'category' : 'range',
                                        'type' : 'RANGE_DIRECTION_CHANGED_TO_HIGH-LOW',
                                        'timestamp' : candle.timestamp,
                                        'price' : candle.low
                                    }

                                else: #High-Low

                                    self.active_range.set_low_when_direction_maintains(candle.low,candle.timestamp)
                                    self.add_fair_value_gap(timestamp_low)
                                    self.del_fair_value_gap(candle)
                                    self.price_at_discount_or_premium(candle)
                                    #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH SAME DIRECTION High-Low at {candle.timestamp}")

                    else: #high_changed == False and low_changed == False

                        self.add_fair_value_gap(timestamp_high if self.active_range.direction == "Low-High" else timestamp_low)
                        self.del_fair_value_gap(candle)
                        self.price_at_discount_or_premium(candle)

            else:

                self.ready = True
                self.window_highs_lows.append(candle)
                active_high = self.active_range.high
                active_low = self.active_range.low
                self.local_lows_highs_and_timestamps()
                
                #UPDATE PREV_RANGE
                self.prev_range = deepcopy(self.active_range)

                high_above_high_range = candle.high >= active_high
                low_below_low_range = candle.low <= active_low

                one_changed = high_above_high_range or low_below_low_range

                if one_changed:

                    if high_above_high_range and low_below_low_range: #both high and low change

                        self.active_range.high = candle.high
                        self.active_range.timestamp_high = candle.timestamp
                        self.active_range.low = candle.low
                        self.active_range.timestamp_low = candle.timestamp
                        self.active_range.direction = "High-Low" if candle.open >= candle.close else "Low-High"
                        self.candles_in_range = []
                        self.candles_in_range.append(candle)
                        self.discount = False
                        self.premium = False

                    else: #~high_above_high_range or ~low_below_low_range

                        if high_above_high_range: #high changed but low remained

                            if self.active_range.direction == "Low-High":

                                self.active_range.set_high_when_direction_maintains(candle.high,candle.timestamp)
                                self.add_fair_value_gap(self.active_range.timestamp_high)
                                self.del_fair_value_gap(candle)
                                self.price_at_discount_or_premium(candle)
                                #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH SAME DIRECTION Low-High at {candle.timestamp}")
                            
                            else: #High-Low

                                self.new_range_when_direction_changes(candle.high,candle.timestamp,"Low-High")
                                #self.active_range.set_high_when_direction_changes(candle.high,candle.timestamp,"Low-High")
                                self.change_candles_in_range(self.active_range.timestamp_low)
                                self.add_fair_value_gap(self.active_range.timestamp_high)
                                self.del_fair_value_gap(candle)
                                self.price_at_discount_or_premium(candle)
                                #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH DIRECTION CHANGING Low-High at {candle.timestamp}")

                                occurrence = {
                                    'category' : 'range',
                                    'type' : 'RANGE_DIRECTION_CHANGED_TO_LOW-HIGH',
                                    'timestamp' : candle.timestamp,
                                    'price' : candle.high
                                }

                                self.events.append(occurrence)

                        else: #low changed but high remained

                            if self.active_range.direction == "Low-High":

                                self.new_range_when_direction_changes(candle.low,candle.timestamp,"High-Low")
                                #self.active_range.set_low_when_direction_changes(candle.low,candle.timestamp,"High-Low")
                                self.change_candles_in_range(self.active_range.timestamp_high)
                                self.add_fair_value_gap(self.active_range.timestamp_low)
                                self.del_fair_value_gap(candle)
                                self.price_at_discount_or_premium(candle)
                                #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH DIRECTION CHANGING High-Low at {candle.timestamp}")

                                occurrence = {
                                    'category' : 'range',
                                    'type' : 'RANGE_DIRECTION_CHANGED_TO_HIGH-LOW',
                                    'timestamp' : candle.timestamp,
                                    'price' : candle.low
                                }

                                self.events.append(occurrence)
                            
                            else: #High-Low

                                self.active_range.set_low_when_direction_maintains(candle.low,candle.timestamp)
                                self.add_fair_value_gap(self.active_range.timestamp_low)
                                self.del_fair_value_gap(candle)
                                self.price_at_discount_or_premium(candle)
                                #print(f"ACTIVE RANGE WAS DEFINED IN TOTAL OF CANDLES BELOW self.back_front_n_candles_for_extremes WITH SAME DIRECTION High-Low at {candle.timestamp}")
                else:

                    #NO LOCAL HIGHS NOR LOWS ARE CREATED BUT ONE NEEDS TO UPDATE WHAT NEEDS UPDATES
                    self.add_fair_value_gap(self.active_range.timestamp_high if self.active_range.direction == "Low-High" else self.active_range.timestamp_low)
                    self.del_fair_value_gap(candle)
                    self.price_at_discount_or_premium(candle)

        else: #len(self.window_highs_lows) == (self.back_front_n_candles_for_extremes*2)+1

            """
            WHAT IS HAPPENING?

            SINCE IT WAS HIGH TO LOW AND BECAME LOW TO HIGH IT IS ASSUMES:

            LAST LOCAL HIGH AFTER THE PREV RANGE END AS THE NEW RANGE START

            PROBLEM : LAST LOCAL HIGH IS NOT ENSURED TO BE THE HIGHEST POINT OF THAT RANGE

            SOLUTION : WHENEVER THE RANGE CHANGES, FROM THE PAST LAST EXTREME TO THE NEW LAST EXTREME

                    - CALCULATE THE CANDLE THAT HAS THE HIGHEST HIGH IF DIRECTION TURNS INTO HIGH-LOW, FOR PREV_RANGE AS LOW-HIGH
                    - OTHERWISE THE CANDLE THAT HAS THE LOWEST LOW IF DIRECTION TURNS INTO LOW-HIGH, FOR PREV_RANGE AS HIGH-LOW
            """

            self.ready = True
            active_high = self.active_range.high
            active_low = self.active_range.low
            self.window_highs_lows.append(candle)

            self.local_lows_highs_and_timestamps()
            
            #UPDATE PREV_RANGE
            self.prev_range = deepcopy(self.active_range)

            current_open = candle.open
            current_close = candle.close
            current_high = candle.high
            current_low = candle.low
            current_timestamp = candle.timestamp

            curr_high_above_range_high = current_high >= active_high
            curr_low_below_range_low = current_low <= active_low

            if curr_high_above_range_high and curr_low_below_range_low: #BOTH RANGE IS CHANGED

                is_bull_candle = True if current_open <= current_close else False
                self.active_range.direction = "Low-High" if is_bull_candle else "High-Low"
                self.active_range.set_range_after_updating_direction(current_high,current_low,current_timestamp,current_timestamp)
                self.candles_in_range = []
                self.candles_in_range.append(candle)
                self.discount = False
                self.premium = False
                print(f" NEW CANDLE IS THE NEW RANGE, BOTH HIGH AT {current_high} AND LOW AT {current_low}, AT {current_timestamp} WITH DIRECTION {self.active_range.direction}")
            
            else: #~curr_high_above_range_high or ~curr_low_below_range_low

                if curr_high_above_range_high == False and curr_low_below_range_low == False: #NO NEW HIGH NOR LOW

                    last_extreme_range_ts = self.active_range.timestamp_high if self.active_range.direction == "Low-High" else self.active_range.timestamp_low
                    #print(f"First_extreme_ts_candles_in_range : {self.candles_in_range[0].timestamp},Last_extreme_ts_candles_in_range : {self.candles_in_range[-1].timestamp},Last_extreme_ts : {last_extreme_range_ts}, Nº Candles in Candles in Range: {len(self.candles_in_range)}")
                    #print(f"Direction Pre-Changes : {self.active_range.direction},Last 15 candles : {self.candles_in_range[-15:]}")
                    candles_in_range_ts = [c.timestamp for c in self.candles_in_range.copy()]
                    idx_last_extreme = candles_in_range_ts.index(last_extreme_range_ts)
                    lst_candles_since_last_extreme = self.candles_in_range[idx_last_extreme:].copy()
                    candles_after_last_extreme = len(lst_candles_since_last_extreme)
                    candles_in_active_range = len(self.candles_in_range) - candles_after_last_extreme
                
                    if candles_after_last_extreme >= 10:

                        active_range_size = self.active_range.high - self.active_range.low
                        most_recent_lst = lst_candles_since_last_extreme[-10:]
                        lst_lows = [c.low for c in most_recent_lst]
                        lst_highs = [c.high for c in most_recent_lst]
                        most_recent_candles_low = min(lst_lows)
                        idx_low = lst_lows.index(most_recent_candles_low)
                        ts_low = most_recent_lst[idx_low].timestamp
                        most_recent_candles_high = max(lst_highs)
                        idx_high = lst_highs.index(most_recent_candles_high)
                        ts_high = most_recent_lst[idx_high].timestamp
                        #candle_size_in_active_range = active_range_size / candles_in_active_range
                        range_past_candles = most_recent_candles_high - most_recent_candles_low
                        #candle_size_in_most_recent_candles = range_past_candles / len(lst_candles_since_last_extreme[-10])
                        pullback_covers_three_quarters = range_past_candles / active_range_size > 0.75
                    
                        if self.active_range.direction == "Low-High":

                            most_recent_range_falls = ts_high < ts_low

                            if pullback_covers_three_quarters:

                                if most_recent_range_falls:

                                    self.active_range.direction = "High-Low"
                                    self.active_range.set_range_after_updating_direction(most_recent_candles_high,most_recent_candles_low,ts_high,ts_low)

                                    self.change_candles_in_range(self.active_range.timestamp_high)
                                    self.add_fair_value_gap(self.active_range.timestamp_low)
                                    self.del_fair_value_gap(candle)
                                    self.price_at_discount_or_premium(candle)

                                
                                else:

                                    if ts_high == ts_low:

                                        if most_recent_lst[idx_high].close >= most_recent_lst[idx_high].open:

                                            self.active_range.direction = "High-Low"
                                            self.active_range.set_range_after_updating_direction(most_recent_candles_high,most_recent_candles_low,ts_high,ts_low)

                                            self.change_candles_in_range(self.active_range.timestamp_high)
                                            self.add_fair_value_gap(self.active_range.timestamp_low)
                                            self.del_fair_value_gap(candle)
                                            self.price_at_discount_or_premium(candle)
                                
                            else: #BASICALLY THE RANGE CONTINUES AS IT IS 

                                self.add_fair_value_gap(self.active_range.timestamp_high)
                                self.del_fair_value_gap(candle)
                                self.price_at_discount_or_premium(candle)

                        else: #"High-Low"

                            most_recent_range_climbs = ts_high > ts_low

                            if pullback_covers_three_quarters:

                                if most_recent_range_climbs:

                                    self.active_range.direction = "Low-High"
                                    self.active_range.set_range_after_updating_direction(most_recent_candles_high,most_recent_candles_low,ts_high,ts_low)

                                    self.change_candles_in_range(self.active_range.timestamp_low)
                                    self.add_fair_value_gap(self.active_range.timestamp_high)
                                    self.del_fair_value_gap(candle)
                                    self.price_at_discount_or_premium(candle)
                                
                                else:

                                    if ts_high == ts_low:

                                        if most_recent_lst[idx_high].close >= most_recent_lst[idx_high].open:

                                            self.active_range.direction = "Low-High"
                                            self.active_range.set_range_after_updating_direction(most_recent_candles_high,most_recent_candles_low,ts_high,ts_low)

                                            self.change_candles_in_range(self.active_range.timestamp_low)
                                            self.add_fair_value_gap(self.active_range.timestamp_high)
                                            self.del_fair_value_gap(candle)
                                            self.price_at_discount_or_premium(candle)
                            
                            else: #BASICALLY THE RANGE CONTINUES AS IT IS 

                                self.add_fair_value_gap(self.active_range.timestamp_low)
                                self.del_fair_value_gap(candle)
                                self.price_at_discount_or_premium(candle)

                    else: #NOT EVEN 10 CANDLES AS PULL BACK SO DON'T DO ANYTHING

                        self.add_fair_value_gap(self.active_range.timestamp_high if self.active_range.direction == "Low-High" else self.active_range.timestamp_low)
                        self.del_fair_value_gap(candle)
                        self.price_at_discount_or_premium(candle)

                    # if self.active_range.direction == "Low-High":

                    #     if len(self.lst_local_lows) != 0:

                    #         prev_ts_low = self.active_range.timestamp_low
                    #         self.range_low_adjust_to_local_low(curr_high_above_range_high)
                    #         upd_ts_low = self.active_range.timestamp_low
                    #         new_local_low = prev_ts_low != upd_ts_low
                    #         if new_local_low :
                    #             self.change_candles_in_range(self.active_range.timestamp_low)
                    #         self.add_fair_value_gap(self.active_range.timestamp_high)
                    #         self.del_fair_value_gap(candle)
                    #         self.price_at_discount_or_premium(candle)

                    #     else:

                    #         # OUTSIDE OF THE RANGE SO NO FAIR VALUE GAP ADDITION THAT ONLY OCCURS 
                    #         self.add_fair_value_gap(self.active_range.timestamp_high)
                    #         self.del_fair_value_gap(candle)
                    #         self.price_at_discount_or_premium(candle)

                    #     #     print(f"EMPTY LIST OF LOCAL LOWS, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH LOW AT {self.active_range.low} AND HIGH AT {self.active_range.high} 7")
                    
                    # else:#"High-Low"

                    #     if len(self.lst_local_highs) != 0:

                    #         prev_ts_high = self.active_range.timestamp_high
                    #         self.range_high_adjust_to_local_high(curr_low_below_range_low)
                    #         upd_ts_high = self.active_range.timestamp_high
                    #         new_local_high = prev_ts_high != upd_ts_high
                    #         if new_local_high:
                    #             self.change_candles_in_range(self.active_range.timestamp_high)
                    #         self.add_fair_value_gap(self.active_range.timestamp_low)
                    #         self.del_fair_value_gap(candle)
                    #         self.price_at_discount_or_premium(candle)

                    #     else:

                    #         self.add_fair_value_gap(self.active_range.timestamp_low)
                    #         self.del_fair_value_gap(candle)
                    #         self.price_at_discount_or_premium(candle)

                    #     #     print(f"EMPTY LIST OF LOCAL HIGHS, SO RANGE REMAINED AT EQUAL TO PREVIOUS ONE, DIRECTION {self.active_range.direction} WITH HIGH AT {self.active_range.high} AND LOW AT {self.active_range.low} 14")

                elif curr_high_above_range_high == True and curr_low_below_range_low == False: #NEW HIGH

                    """REGARDING CONTINUATION WHEN A NEW HIGH IS FORMED INSTEAD ONLY LOCAL LOWS TO CONTINUE STRUCTURE DO:

                        TAKE THE RANGE FROM THE PAST EXTREME OF THE LAST RANGE TILL THE NEW EXTREME AND PICK THE LOWEST POINT;"""

                    if self.active_range.direction == "Low-High":

                        self.active_range.set_high_when_direction_maintains(current_high,current_timestamp)

                        if len(self.lst_local_lows) != 0:

                            prev_ts_low = self.active_range.timestamp_low
                            self.range_low_adjust_to_local_low(curr_high_above_range_high)
                            upd_ts_low = self.active_range.timestamp_low
                            new_local_low = prev_ts_low != upd_ts_low
                            if new_local_low :
                                self.change_candles_in_range(self.active_range.timestamp_low)
                            self.add_fair_value_gap(self.active_range.timestamp_high)
                            self.del_fair_value_gap(candle)
                            self.price_at_discount_or_premium(candle)
                        
                        else:

                            self.add_fair_value_gap(self.active_range.timestamp_high)
                            self.del_fair_value_gap(candle)
                            self.price_at_discount_or_premium(candle)

                        #     print(f"NEW ABSOLUTE HIGH IN RANGE AT {self.active_range.high}, AND NO UPDATES ON THE LOW KEEPING STEADY AT {self.active_range.low} AND MAINTAING THE OVERALL DIRECTION {self.active_range.direction} 8")

                    else: #"High-Low"

                        prev_range_dir = self.active_range.direction
                        self.new_range_when_direction_changes(current_high,current_timestamp,"Low-High")
                        #self.active_range.set_high_when_direction_changes(current_high,current_timestamp,"Low-High")
                        self.change_candles_in_range(self.active_range.timestamp_low)
                        self.add_fair_value_gap(self.active_range.timestamp_high)
                        self.del_fair_value_gap(candle)
                        print(f"RANGE CHANGED FROM {prev_range_dir} TO {self.active_range.direction} CONTINUING WITH THE SAME LOW AT {self.active_range.low} AND NEW HIGH AT {self.active_range.high}")


                else: #curr_high_above_range_high == False and curr_low_below_range_low == True, SO NEW LOW

                    """REGARDING CONTINUATION WHEN A NEW HIGH IS FORMED INSTEAD ONLY LOCAL LOWS TO CONTINUE STRUCTURE DO:

                    TAKE THE RANGE FROM THE PAST EXTREME OF THE LAST RANGE TILL THE NEW EXTREME AND PICK THE LOWEST POINT;"""

                    if self.active_range.direction == "Low-High":

                        prev_range_dir = self.active_range.direction
                        self.new_range_when_direction_changes(current_low,current_timestamp,"High-Low")
                        #self.active_range.set_low_when_direction_changes(current_low,current_timestamp,"High-Low")
                        self.discount = False
                        self.premium = False
                        self.change_candles_in_range(self.active_range.timestamp_high)
                        self.add_fair_value_gap(self.active_range.timestamp_low)
                        self.del_fair_value_gap(candle)
                        self.price_at_discount_or_premium(candle)
                        print(f"RANGE CHANGED FROM {prev_range_dir} TO {self.active_range.direction} CONTINUING WITH THE SAME HIGH AT {self.active_range.high} AND NEW LOW AT {self.active_range.low}")

                    else: #"High-Low"

                        self.active_range.set_low_when_direction_maintains(current_low,current_timestamp)
                        
                        if len(self.lst_local_highs) != 0:

                            prev_ts_high = self.active_range.timestamp_high
                            self.range_high_adjust_to_local_high(curr_low_below_range_low)
                            upd_ts_high = self.active_range.timestamp_high
                            new_local_high = prev_ts_high != upd_ts_high
                            if new_local_high:
                                self.change_candles_in_range(self.active_range.timestamp_high)
                            self.add_fair_value_gap(self.active_range.timestamp_low)
                            self.del_fair_value_gap(candle)
                            self.price_at_discount_or_premium(candle)
                        
                        else:

                            self.add_fair_value_gap(self.active_range.timestamp_low)
                            self.del_fair_value_gap(candle)
                            self.price_at_discount_or_premium(candle)

                        #     print(f"NEW ABSOLUTE LOW IN RANGE AT {self.active_range.low}, AND NO UPDATES ON THE HIGH KEEPING STEADY AT {self.active_range.high} AND MAINTAING THE OVERALL DIRECTION {self.active_range.direction} 15")
        # expected_first = (
        #     self.active_range.timestamp_low
        #     if self.active_range.direction == "Low-High"
        #     else self.active_range.timestamp_high
        # )

        # actual_first = self.candles_in_range[0].timestamp

        # if expected_first != actual_first:
        #     print("INVARIANT BROKEN")
        #     print("Direction:", self.active_range.direction)
        #     print("Expected first:", expected_first)
        #     print("Actual first:", actual_first)
        #     raise RuntimeError("candles_in_range out of sync")


    def snapshot(self):

        return {
            "current_candle" : {
                "current_candle_ts" : self.candles_in_range[-1].timestamp, #USED TO SEE IF TS OFF LOCAL HIGHS AND LOWS IS ALSO AT THE SAME TIME AS NEWEST CANDLE
                "current_candle_open" : self.candles_in_range[-1].open,
                "current_candle_high" : self.candles_in_range[-1].high,
                "current_candle_low" : self.candles_in_range[-1].low,
                "current_candle_close" : self.candles_in_range[-1].close,
                "current_candle_tick_vol" : self.candles_in_range[-1].tick_volume
            },
            "active_range": self.active_range,
            "prev_range": self.prev_range,
            "local_highs": self.lst_local_highs[-10:],
            "local_highs_ts": self.lst_local_highs_ts[-10:],
            "local_lows": self.lst_local_lows[-10:],
            "local_lows_ts": self.lst_local_lows_ts[-10:],
            "fv_gaps" : self.dict_time_fvg,
            "ready": self.ready
        }
    
    def flush_events(self):

        events = self.events.copy()
        self.events.clear()
        return events

#INDICATORS

class ATR:

    def __init__(self,n_candles_considered:int,role:str):

        self.n_candles_considered = n_candles_considered
        self.role = role

        self.lst_candles_used = deque(maxlen = n_candles_considered) #ONLY COLLECTS THE LAST self.length_sma
        self.value = None
        self.ready = False
        self.last_tr = None

    
    def update(self,candle:Candle):

        if len(self.lst_candles_used) < self.n_candles_considered:

            if len(self.lst_candles_used) == self.n_candles_considered - 1:

                self.lst_candles_used.append(candle)

                total_true_ranges = 0

                for i in range(len(self.lst_candles_used)):

                    c = self.lst_candles_used[i]

                    if i == 0:

                        true_range = c.high - c.low
                        total_true_ranges += true_range
                    
                    else:

                        prev_c = self.lst_candles_used[i-1]
                        prev_close = prev_c.close
                        current_high = c.high
                        current_low = c.low
                        last_candle_range = current_high - current_low
                        abs_val_curr_high_minus_prev_close = abs(current_high-prev_close)
                        abs_val_curr_low_minus_prev_close = abs(current_low-prev_close)
                        atr_val = max(last_candle_range,abs_val_curr_high_minus_prev_close,abs_val_curr_low_minus_prev_close)
                        self.last_tr = atr_val
                        total_true_ranges += atr_val
                
                self.value = total_true_ranges / self.n_candles_considered
                self.ready = True
            
            else:

                self.lst_candles_used.append(candle)

        else:

            previous_close = self.lst_candles_used[-1].close
            self.lst_candles_used.append(candle)
            current_high = self.lst_candles_used[-1].high
            current_low = self.lst_candles_used[-1].low
            last_candle_range = current_high - current_low
            abs_val_curr_high_minus_prev_close = abs(current_high-previous_close)
            abs_val_curr_low_minus_prev_close = abs(current_low-previous_close)
            true_range = max(last_candle_range,abs_val_curr_high_minus_prev_close,abs_val_curr_low_minus_prev_close)
            self.last_tr = true_range
            atr = (true_range + ((self.n_candles_considered-1) * self.value)) / self.n_candles_considered
            self.value = atr

class ADX:

    def __init__(self,atr_class:ATR,role:str):

        self.atr = atr_class
        self.role = role

        self.lst_plus_dm = deque(maxlen = self.atr.n_candles_considered)
        self.lst_minus_dm = deque(maxlen = self.atr.n_candles_considered)
        self.lst_dx = deque(maxlen = self.atr.n_candles_considered)

        self.prev_high = None
        self.prev_low = None
        self.smooth_plus_dm = None
        self.smooth_minus_dm = None
        self.prev_value = None
        self.value = None
        self.ready = False
    
    def update(self,candle:Candle):

        if self.prev_high == None:

            self.prev_high = candle.high
            self.prev_low = candle.low
            self.atr.update(candle)

        else:

            plus_dm = candle.high - self.prev_high
            minus_dm = self.prev_low - candle.low

            if len(self.lst_plus_dm) < self.atr.n_candles_considered :

                self.atr.update(candle)
                tr_smooth_val = self.atr.last_tr

                if len(self.lst_plus_dm) == self.atr.n_candles_considered - 1:

                    self.lst_plus_dm.append(plus_dm if (plus_dm > minus_dm and plus_dm > 0) else 0)
                    self.lst_minus_dm.append(minus_dm if (minus_dm > plus_dm and minus_dm > 0) else 0)

                    running_sum_plus_dm = sum(self.lst_plus_dm)
                    running_sum_minus_dm = sum(self.lst_minus_dm)

                    self.smooth_plus_dm = running_sum_plus_dm
                    self.smooth_minus_dm = running_sum_minus_dm

                    plus_di = (self.smooth_plus_dm / tr_smooth_val) * 100 if tr_smooth_val != 0 else 0
                    minus_di = (self.smooth_minus_dm / tr_smooth_val) * 100 if tr_smooth_val != 0 else 0
                    dx = (abs(plus_di-minus_di)/abs(plus_di+minus_di)) * 100 if plus_di+minus_di != 0 else 0
                    self.lst_dx.append(dx)
                
                else:

                    self.lst_plus_dm.append(plus_dm if (plus_dm > minus_dm and plus_dm > 0) else 0)
                    self.lst_minus_dm.append(minus_dm if (minus_dm > plus_dm and plus_dm > 0) else 0)

            else:

                prev_tr = self.atr.last_tr
                self.atr.update(candle)
                tr_smooth_val = self.atr.last_tr
                self.lst_plus_dm.append(plus_dm if (plus_dm > minus_dm and plus_dm > 0) else 0)
                self.lst_minus_dm.append(minus_dm if (minus_dm > plus_dm and minus_dm > 0) else 0)

                self.smooth_plus_dm = self.smooth_plus_dm - (self.smooth_plus_dm / self.atr.n_candles_considered) + self.lst_plus_dm[-1]
                self.smooth_minus_dm = self.smooth_minus_dm - (self.smooth_minus_dm / self.atr.n_candles_considered) + self.lst_minus_dm[-1]
                
                smooth_tr = prev_tr - (prev_tr / self.atr.n_candles_considered) + tr_smooth_val

                plus_di = (self.smooth_plus_dm / smooth_tr) * 100 if smooth_tr != 0 else 0
                minus_di = (self.smooth_minus_dm / smooth_tr) * 100 if smooth_tr != 0 else 0
                dx = (abs(plus_di-minus_di)/abs(plus_di+minus_di)) * 100 if plus_di+minus_di != 0 else 0
                
                if len(self.lst_dx) < self.atr.n_candles_considered:

                    if len(self.lst_dx) == self.atr.n_candles_considered - 1:

                        self.lst_dx.append(dx)
                        self.value = sum(self.lst_dx) / self.atr.n_candles_considered
                        self.prev_value = self.value
                    
                    else:

                        self.lst_dx.append(dx)

                else:

                    self.lst_dx.append(dx)
                    self.value = (self.prev_value * (self.atr.n_candles_considered - 1) + dx) / self.atr.n_candles_considered
                    self.prev_value = self.value
        
        self.prev_high = candle.high
        self.prev_low = candle.low

class Chop_Index:

    def __init__(self,n_candles_considered:int,role:str):

        self.n_candles_considered = n_candles_considered
        self.lst_values_used = deque(maxlen = n_candles_considered+1)
        self.atr = deque(maxlen = n_candles_considered)
        self.role = role

        self.max_range = 0
        self.value = None
        self.ready = False

    def update(self,candle:Candle):

        if len(self.lst_values_used) < self.n_candles_considered + 1:

            self.lst_values_used.append(candle)

            if len(self.lst_values_used) == self.n_candles_considered + 1:

                for i in range(1,len(self.lst_values_used)):

                    prev_c = self.lst_values_used[i-1]
                    c = self.lst_values_used[i]

                    #MAX_HIGH(n) - MAX_LOW(n) CALCULATION
                    high = c.high
                    low = c.low
                    range = high - low 
                    self.max_range = range if range > self.max_range else self.max_range

                    #CANDLES_ATRs

                    prev_close = prev_c.close
                    abs_val_curr_high_minus_prev_close = abs(high-prev_close)
                    abs_val_curr_low_minus_prev_close = abs(low-prev_close)
                    candle_atr = max(range,abs_val_curr_high_minus_prev_close,abs_val_curr_low_minus_prev_close)
                    self.atr.append(candle_atr)
                
                sum_atr = sum(self.atr)
                chop_index = 100 * (math.log10(sum_atr/self.max_range)/math.log10(self.n_candles_considered))
                self.value = chop_index

        else:

            prev_c = self.lst_values_used[-1]
            prev_close = prev_c.close
            self.lst_values_used.append(candle)
            c = self.lst_values_used[-1]
            high = c.high
            low = c.low
            range = high - low
            self.max_range = range if range > self.max_range else self.max_range
            abs_val_curr_high_minus_prev_close = abs(high-prev_close)
            abs_val_curr_low_minus_prev_close = abs(low-prev_close)
            candle_atr = max(range,abs_val_curr_high_minus_prev_close,abs_val_curr_low_minus_prev_close)
            self.atr.append(candle_atr)
            sum_atr = sum(self.atr)
            chop_index = 100 * (math.log10(sum_atr/self.max_range)/math.log10(self.n_candles_considered))
            self.value = chop_index

class Money_Flow_Index: #DON'T HAVE VOLUME, SOME THAT DOESN'T HAVE ANY USEFULNESS

    def __init__(self,n_candles_considered:int,role:str):

        self.n_candles_considered = n_candles_considered
        self.role = role

        self.typical_prices = deque(maxlen = n_candles_considered+1) #ONLY COLLECTS THE LAST self.length_sma
        self.changes = deque(maxlen = n_candles_considered)
        self.volumes = deque(maxlen = n_candles_considered)
        self.value = None
        self.ready = False

    def update(self,candle:Candle):

        self.volumes.append(candle.tick_volume)
        typical_price = (candle.close + candle.high + candle.low) / 3
                
        if len(self.typical_prices) < self.n_candles_considered + 1:

            self.typical_price.append(typical_price)

            if len(self.typical_prices) == self.n_candles_considered + 1:

                for i in range(1,len(self.typical_prices)):

                    t_price = self.typical_prices[i]
                    t_prev_price = self.typical_prices[i-1]
                    change = t_price - t_prev_price
                    self.changes.append(change)
                
                positive_money_flows = 0
                negative_money_flows = 0
                for i in range(len(self.changes)):

                    change = self.changes[i]

                    if change <= 0:

                        negative_money_flows += self.typical_prices[i+1] * self.volumes[i]
                    
                    else:

                        positive_money_flows += self.typical_prices[i+1] * self.volumes[i]
                
                mf_ratio = positive_money_flows / negative_money_flows
                mfi = 100 - (100 / (1 + mf_ratio))
                self.value = mfi

        else:

            t_price = self.typical_prices[i]
            t_prev_price = self.typical_prices[i-1]
            change = t_price - t_prev_price
            self.changes.append(change)

            positive_money_flows = 0
            negative_money_flows = 0
            for i in range(len(self.changes)):

                change = self.changes[i]

                if change <= 0:

                    negative_money_flows += self.typical_prices[i+1] * self.volumes[i]
                
                else:

                    positive_money_flows += self.typical_prices[i+1] * self.volumes[i]
            
            mf_ratio = positive_money_flows / negative_money_flows
            mfi = 100 - (100 / (1 + mf_ratio))
            self.value = mfi

class RSI:

    def __init__(self,period_size_gains_losses:int,role:str):

        self.period_size = period_size_gains_losses
        self.role = role
        self.lst_gains_losses = deque() #ONLY COLLECTS THE LAST self.length_sma

        self.value = None
        self.ready = False
        self.cum_gain = 0
        self.cum_loss = 0

        self.avg_gain = 0
        self.avg_loss =  0
    
    def update(self,candle:Candle):

        close = candle.close
        open = candle.open
        gain_loss_pct = (close / open) - 1

        if len(self.lst_gains_losses) < self.period_size:

            #NO NEED TO REMOVE LAST PERIOD BECAUSE IT IS BELOW PERIOD SIZE

            if gain_loss_pct <= 0:

                self.cum_loss += abs(gain_loss_pct)
                self.cum_gain += 0
            
            else:

                self.cum_loss += 0
                self.cum_gain += gain_loss_pct
            
            self.lst_gains_losses.append(gain_loss_pct)
            
            avg_gain = self.cum_gain / len(self.lst_gains_losses)
            avg_loss = self.cum_loss / len(self.lst_gains_losses)

            self.value = None if len(self.lst_gains_losses) < self.period_size else 100 - (100 / (1 + (avg_gain / avg_loss)))
            self.ready = False if len(self.lst_gains_losses) < self.period_size else True
        
        else: #len(self.lst_gains_losses) >= self.period_size: #>= self.period_size

            prev_avg_gain = self.cum_gain / len(self.lst_gains_losses) if len(self.lst_gains_losses) == self.period_size else self.avg_gain
            prev_avg_loss = self.cum_loss / len(self.lst_gains_losses) if len(self.lst_gains_losses) == self.period_size else self.avg_loss

            self.lst_gains_losses.append(gain_loss_pct)

            current_gain = gain_loss_pct if gain_loss_pct > 0 else 0
            current_loss = abs(gain_loss_pct) if gain_loss_pct <=0 else 0

            self.avg_gain = prev_avg_gain * ((self.period_size-1)/self.period_size) + current_gain * (1/self.period_size)
            self.avg_loss = prev_avg_loss * ((self.period_size-1)/self.period_size) + current_loss * (1/self.period_size)

            rs = self.avg_gain / self.avg_loss
            self.value = 100 - (100 / (1 + rs))
            self.ready = True

class SMA:

    def __init__(self,length_sma:int,role:str):

        self.length_sma = length_sma
        self.role = role
        self.window = deque(maxlen = self.length_sma) #ONLY COLLECTS THE LAST self.length_sma

        self.value = None
        self.running_sum = 0
        self.ready = False
    
    def update(self,candle:Candle):

        close = candle.close
        new_val = close

        if len(self.window) < self.length_sma:

            self.running_sum += new_val
            self.value = None if len(self.window) != self.length_sma - 1 else self.running_sum / self.length_sma
            self.ready = False if len(self.window) != self.length_sma - 1 else True
            self.window.append(close)
            #OR self.value = sum(self.window) / len(self.window)
        
        else:
            
            oldest_val = self.window[0]
            self.running_sum -= oldest_val
            self.running_sum += new_val
            self.value = self.running_sum / self.length_sma
            self.ready = True
            self.window.append(close)

class EMA:

    def __init__(self,length_ema:int,smooth_strength:int,role:str):

        self.length_sma = length_ema
        self.smooth_strength = smooth_strength
        self.role = role
        self.window = deque(maxlen = self.length_ema) #ONLY COLLECTS THE LAST self.length_sma

        self.smooth_factor = self.smooth_strength / (self.length_sma + 1) #THE HIGHER THE SMOOTH STRENGTH, THE HIGHER THE IMPORTANCE OF THE PAST VALUE
        self.prev_value = None
        self.value = None
        self.running_sum = 0
        self.ready = False
        
    
    def update(self,candle:Candle):

        close = candle.close
        new_val = close

        if len(self.window) < self.length_sma:

            self.running_sum += new_val
            self.value = None if len(self.window) != self.length_sma - 1 else self.running_sum / self.length_sma
            self.ready = False if len(self.window) != self.length_sma - 1 else True
            self.window.append(close)
            #OR self.value = sum(self.window) / len(self.window)
        
        else:
            
            self.prev_value = self.value
            self.value = (close * self.smooth_factor) * (self.prev_value * (1-(self.smooth_factor)))  
            self.ready = True
            self.window.append(close)

class MACD:

    """
    self.value > 0 : Bullish
    self.value < 0 : Bearish
    
    """

    def __init__(self,lower_period_ema:EMA,higher_period_ema:EMA,ema_periods_difference_line:int,role:str):

        self.lower_period_ema = lower_period_ema
        self.higher_period_ema = higher_period_ema
        self.periods_ema_difference = ema_periods_difference_line
        self.role = role
        self.window = deque(maxlen = self.periods_ema_difference)

        self.ready = None
        self.macd_line = None
        self.signal_line = None
        self.value = None
        self.change_from_prev_val = None
        self.change_storage = []
        self.significant_change = None
    
    def find_signal_line(self):

        smooth_strength = self.lower_period_ema.smooth_strength
        length_ema = self.periods_ema_difference
        smooth_fac = smooth_strength / length_ema

        if self.signal_line == None:

            running_sum = sum(self.window)
            signal_line = running_sum / length_ema

        else:

            prev_value = self.signal_line
            curr_value = self.macd_line
            signal_line = (curr_value * smooth_fac) * (prev_value * (1-(smooth_fac)))
        
        return signal_line
    
    
    def curr_chg_abv_avg(self):

        avg_chg = sum(self.change_storage) / len(self.change_storage)
        last_chg = self.change_storage[-1]

        return True if last_chg >= avg_chg else False
    

    def update(self,candle:Candle):

        self.lower_period_ema.update(candle)
        self.higher_period_ema.update(candle)

        if self.lower_period_ema.value != None and self.higher_period_ema.value != None:

            self.macd_line = self.lower_period_ema.value - self.higher_period_ema.value

            if len(self.window) < self.periods_ema_difference:

                if len(self.window) == self.periods_ema_difference - 1:

                    self.window.append(self.macd_line)
                    self.signal_line = self.find_signal_line()
                    self.value = self.macd_line - self.signal_line
                    self.ready = True
                
                else:

                    self.window.append(self.macd_line)
            
            else:   

                prev_value = self.value
                self.window.append(self.macd_line)
                self.signal_line = self.find_signal_line()
                self.value = self.macd_line - self.signal_line
                self.change_from_prev_val = self.value - prev_value
                self.change_storage.append(self.change_from_prev_val)
                self.significant_change = self.curr_chg_abv_avg()
                self.ready = True

class Bollinger_Bands:

    def __init__(self,middle_band:SMA,distance_from_middle_in_st_devs:int,role:str):

        self.middle_band = middle_band
        self.distance_in_st_devs = distance_from_middle_in_st_devs
        self.role = role
        self.st_devs_above = deque(maxlen=self.middle_band.length_sma)
        self.st_devs_below = deque(maxlen=self.middle_band.length_sma)

        self.value_above_mid = None
        self.value_below_mid = None
        self.ready = False
        
    def update(self,candle:Candle):

        if self.middle_band.ready != True:

            self.middle_band.update(candle)

            if self.middle_band.ready == True:

                array_window = np.array(self.middle_band.window)
                st_dev_array = array_window.std()
                self.value_above_mid = self.middle_band.value + self.distance_in_st_devs * st_dev_array
                self.value_below_mid = self.middle_band.value - self.distance_in_st_devs * st_dev_array
                self.st_devs_above.append(self.value_above_mid)
                self.st_devs_below.append(self.value_below_mid)
                self.ready = True

        else:

            self.middle_band.update(candle)
            array_window = np.array(self.middle_band.window)
            st_dev_array = array_window.std()
            self.value_above_mid = self.middle_band.value + self.distance_in_st_devs * st_dev_array
            self.value_below_mid = self.middle_band.value - self.distance_in_st_devs * st_dev_array
            self.st_devs_above.append(self.value_above_mid)
            self.st_devs_below.append(self.value_below_mid)

class Stochastic_Oscillator:

    def __init__(self,n_periods_used:int,n_periods_for_slow_stochastic:int,role:str):

        self.n_periods = n_periods_used
        self.n_slow_stoch = n_periods_for_slow_stochastic
        self.role = role
        self.window = deque(maxlen=self.n_periods)

        self.ready = False
        self.fast_stochastic = None
        self.prev_fast_stochastic = None
        self.slow_stochastic_lst = deque(maxlen=self.n_slow_stoch)
        self.slow_stochastic = None
        self.prev_fast_stochastic = None
        self.fast_crossing_above_slow = None
        self.fast_crossing_below_slow = None

        #fast_stoch crossing above slow_stoch signals buy. Contrarily fast_stoch crossing below slow_stoch signals sell.
    
    def update(self,candle:Candle):

        if len(self.window) < self.n_periods:

            if len(self.window) == self.n_periods - 1:

                self.window.append(candle)
                current_close = self.window[-1].close
                window_high = max([c.high for c in self.window])
                window_low = min([c.low for c in self.window])
                self.fast_stochastic = ((current_close - window_low) / (window_high - window_low)) * 100
                self.slow_stochastic_lst.append(self.fast_stochastic)

            else:

                self.window.append(candle)
        
        else:

            self.prev_fast_stochastic = self.fast_stochastic
            self.prev_slow_stochastic = self.slow_stochastic
            self.window.append(candle)
            current_close = self.window[-1].close
            window_high = max([c.high for c in self.window])
            window_low = min([c.low for c in self.window])
            self.fast_stochastic = ((current_close - window_low) / (window_high - window_low)) * 100
            self.slow_stochastic_lst.append(self.fast_stochastic)

            if len(self.slow_stochastic_lst) == self.n_slow_stoch:

                self.slow_stochastic = sum(self.slow_stochastic_lst) / self.n_slow_stoch
            
            no_none_vals = self.prev_fast_stochastic != None and self.prev_slow_stochastic != None and self.fast_stochastic != None and self.slow_stochastic_lst != None

            if no_none_vals:

                yesterday_fast_below_slow = self.prev_fast_stochastic < self.prev_slow_stochastic
                today_fast_above_slow = self.prev_fast_stochastic > self.prev_slow_stochastic

                self.fast_crossing_above_slow = True if (yesterday_fast_below_slow and today_fast_above_slow) else False

                yesterday_fast_above_slow = self.prev_fast_stochastic > self.prev_slow_stochastic
                today_fast_below_slow = self.prev_fast_stochastic < self.prev_slow_stochastic

                self.fast_crossing_below_slow = True if (yesterday_fast_above_slow and today_fast_below_slow) else False

#SINGULAR TIMEFRAME ENGINE

class Engine:

    def __init__(self,indicators,structure,strat_signal):

        #Indicators created by classes
        self.indicators = indicators

        #Structure created by class structure
        self.structure = structure

        #StrategyContext

        self.context = StrategyContext(
            indicator_values = None,
            structure_snapshot = None,
            structure_events = None,
            timestamp = None

        ) #Starts empty, is filled on candle and then things are cleared? 

        #Strategy
        self.strategy = strat_signal

    def on_candle(self,candle:Candle):

        #UPDATING INDICATORS
        values = {}

        for ind in self.indicators:

            indicator_class = self.indicators[ind]
            role = self.indicators[ind].role
            indicator_class.update(candle)
            values[role] = indicator_class.value
        
        self.context.indicator_values = values

        #UPDATING STRUCTURE
        self.structure.update(candle)
        current_struct = self.structure.snapshot()
        events = self.structure.flush_events() #IT STORES THE EVENTS BUT ATTRIBUTE OF structure events is cleared
        self.context.structure_snapshot = current_struct
        self.context.structure_events = events
        self.context.timestamp = candle.timestamp

        #SEND SIGNAL
        signal = self.strategy.signal_generation(self.context)

        return signal

#INSTRUMENT IN WHICH THE BACKTEST RUNS

class Instrument:

    def __init__(self,symbol:str,pip_size:float,tick_size:float,contract_size:float,spread:float):

        self.symbol = symbol
        self.pip_size = pip_size
        self.tick_size = self.pip_size / 10 #minimum allowable price increment by which a tradable asset can move , pipettes in FX
        self.spread = spread

        # spread: float

        # contract_size: float

        # min_lot: float
        # lot_step: float

        # commission_per_lot: float

    """USE IT TO CHECK ON OTHER INSTRUMENTS, THEN ON POSITION YOU ADD A PROPERTY
       INSTRUMENT WHERE YOU SPECIFY SYMBOL AND TICK_SIZE THE INSTRUMENT EQUIVALENT
       TO FX_PIP, BASICALLY UNIT OF ACCOUNTING. IF YOU USE THAT 'spread_in_pips','self.pip'
       CAN DISAPPEAR BECAUSE INSTRUMENT CLASS WILL ACCOUNT FOR THAT
    """

#SIGNALLING OFF INTENTION OF CREATING A MARKET ORDER

@dataclass
class TradeIntent:
    direction: str
    timestamp: datetime
    timeframes: dict
    confidence: float = 1.0

#MATCHING OFF TIMEFRAMES TO MAKE THE ORDER VALID

class ConfluenceEngine:

    def __init__(self,latest_setup_dict:dict):

        self.latest_setup = latest_setup_dict 

        #THEN WHEN INSTANTIATING ConfluenceEngine I pass the self.latest_setup from MultiTfEngine

    def is_valid_confluence(self):

        direction_lst = []
        var_setup = not None
        for key in self.latest_setup:

            value_of_the_key = self.latest_setup[key] #EITHER 'None' OR 'SetupEvent' Object From strategies files on folder

            if value_of_the_key == None:

                var_setup = None
                direction_lst.append(var_setup)
            
            else:

                direction_lst.append(value_of_the_key.direction)

        n_buy = direction_lst.count("BUY")
        n_sell = direction_lst.count("SELL")

        if var_setup == None: #THIS MEANS THAT IF ONE OF THEM IS 'None' THIS WILL RETURN FALSE
            return False

        return (
            n_buy == len(direction_lst) or n_sell == len(direction_lst)
        )

    def update(self, prev_setups: dict ,setups: dict):

        smallest_tf = list(prev_setups.keys())[0]
        tf_after_small = list(prev_setups.keys())[1] #ASSUMING THE STRATEGY USES 3 TFS
        prev_timestamp = None if prev_setups[tf_after_small] == None else prev_setups[tf_after_small].timestamp

        for tf, event in setups.items():
            if event is not None:
                self.latest_setup[tf] = event
    
        if self.is_valid_confluence(): #ALL TIMEFRAMES GIVE EITHER BUY OR SELL 

            timestamp_differ = prev_timestamp != self.latest_setup[tf_after_small].timestamp

            if timestamp_differ:

                return TradeIntent(
                    direction=self.latest_setup[smallest_tf].direction,
                    timestamp=self.latest_setup[smallest_tf].timestamp,
                    timeframes=self.latest_setup.copy()
                )

        return None

#MARKET SIGNALS FOR CREATION OF POSITION

@dataclass
class MarketOrder:

    symbol: str
    direction: str
    timestamp: datetime
    status: str = "PENDING"
    fill_price: float = None
    fill_timestamp: datetime = None


#POSITION CREATION & MODELLING OFF ENTRIES AND RISK

class Position:

    def __init__(self,direction:str,entry_p:float,sl:float,tp:float,pct_risk:float,spread_in_pips:float,open_time:datetime):
    #THIS ONLY EXISTS IF ALL THE THREE TIMEFRAMES MATCH AS SUPPOSED AND SIGNAL BECOMES TRUE
        self.direction = direction
        self.entry_p = entry_p
        self.sl = sl
        self.tp = tp
        self.pct_risk = pct_risk
        self.spread_in_pips = spread_in_pips
        self.open_time = open_time

        self.pip = 0.0001
        self.current_price = None
        self.capital_at_risk = None
        self.close_time = None #NOT KNOWN YET
        self.pips_sl = abs(self.entry_p - self.sl) / self.pip
        self.risk_reward = None
        self.commission = None
        self.pnl = None
        self.result = None
        self.value_added = None #MONETARY CHANGE IN A POSITION FROM TRADE TO TRADE 
        self.ask_bid_mid = None
        self.duration_in_candles = 1
    
    def build_initial_trade_metadata(self,pct_commission_on_loss:float,last_candle:Candle,disposable_balance:float):

        #CONSTRUCTION OF A TRADE DICT

        spread_in_price_movement = self.pip * self.spread_in_pips
        #ENTRY NEVER NEEDS ADJUSTMENTS REGARDLESS OF THE WAY THE GRAPH SHOWS YOU BECAUSE YOU ALWAYS ENTER AT THE BID OR AT THE ASK
        pips_tp = abs(self.entry_p - self.tp) / self.pip
        self.risk_reward = pips_tp / self.pips_sl
        self.capital_at_risk = disposable_balance * self.pct_risk
        self.commission = self.capital_at_risk * pct_commission_on_loss
        self.current_price = last_candle.close
        curr_p_above_entry_p = self.entry_p > self.entry_p
        self.pnl = (((self.current_price - self.entry_p) / self.pip) / self.pips_sl) * self.capital_at_risk if self.direction == "BUY" else (((self.entry_p - self.current_price) / self.pip) / self.pips_sl) * self.capital_at_risk
        self.value_added = self.pnl


        """FOR BACKTESTS THIS ADJUSTMENTS MAKE SENSE BUT IN LIVE TRADING SYSTEMS THE BROKER ALREADY INTEGRATES THESE THINGS"""

        # if self.ask_bid_mid == "MID":

        #     spread_deviation = (self.pip * self.spread_in_pips) / 2
        #     self.entry_p = self.entry_p + (spread_in_price_movement/2) if self.direction == "BUY" else self.entry_p - (spread_in_price_movement/2)
        #     self.tp = self.tp + (spread_in_price_movement/2) if self.direction == "BUY" else self.tp - (spread_in_price_movement/2)
        #     self.sl = self.sl + (spread_in_price_movement/2) if self.direction == "BUY" else self.sl - (spread_in_price_movement/2)
        #     self.pips_sl = abs(self.entry_p - self.sl) / self.pip
        #     pips_tp = abs(self.entry_p - self.tp) / self.pip
        #     self.risk_reward = pips_tp / self.pips_sl
        #     self.capital_at_risk = available_balance * self.pct_risk
        #     self.commission = self.capital_at_risk * pct_commission_on_loss
        #     self.current_price = last_candle.close - spread_deviation if self.direction == "BUY" else last_candle.close + spread_deviation
        #     self.pnl = (((self.current_price - self.entry_p) / self.pip) / self.pips_sl) * self.capital_at_risk if self.direction == "BUY" else ((abs(self.current_price - self.entry_p) / self.pip) / self.pips_sl) * self.capital_at_risk
        
        # elif self.ask_bid_mid == "BID":

        #     self.entry_p = self.entry_p + spread_in_price_movement if self.direction == "BUY" else self.entry_p
        #     self.tp = self.tp if self.direction == "BUY" else self.tp + spread_in_price_movement
        #     self.sl = self.sl if self.direction == "BUY" else self.sl - spread_in_price_movement
        #     self.pips_sl = abs(self.entry_p - self.sl) / self.pip
        #     pips_tp = abs(self.entry_p - self.tp) / self.pip
        #     self.risk_reward = pips_tp / self.pips_sl
        #     self.capital_at_risk = available_balance * self.pct_risk
        #     self.commission = self.capital_at_risk * pct_commission_on_loss
        #     self.current_price = last_candle.close if self.direction == "BUY" else last_candle.close
        #     self.pnl = (((self.current_price - self.entry_p) / self.pip) / self.pips_sl) * self.capital_at_risk if self.direction == "BUY" else ((abs(self.current_price - self.entry_p) / self.pip) / self.pips_sl) * self.capital_at_risk
        
        # else: #self.ask_bid_mid == "ASK":

        #     self.entry_p = self.entry_p if self.direction == "BUY" else self.entry_p - spread_in_price_movement
        #     self.tp = self.tp - spread_in_price_movement if self.direction == "BUY" else self.tp
        #     self.sl = self.sl + spread_in_price_movement if self.direction == "BUY" else self.sl
        #     self.pips_sl = abs(self.entry_p - self.sl) / self.pip
        #     pips_tp = abs(self.entry_p - self.tp) / self.pip
        #     self.risk_reward = pips_tp / self.pips_sl
        #     self.capital_at_risk = available_balance * self.pct_risk
        #     self.commission = self.capital_at_risk * pct_commission_on_loss
        #     self.current_price = last_candle.close if self.direction == "BUY" else last_candle.close
        #     self.pnl = (((self.current_price - self.entry_p) / self.pip) / self.pips_sl) * self.capital_at_risk if self.direction == "BUY" else ((abs(self.current_price - self.entry_p) / self.pip) / self.pips_sl) * self.capital_at_risk



        #QUESTION TO ANSWER, CONDITIONS CAN ONLY BE ANALYZED AT THE CLOSE OF A GIVEN CANDLE
        #MEANING OPENING OF A TRADE CAN ONLY HAPPEN AFTER EVERYTHING IS PROCESSED, RIGHT?
        #MEANING SL AND TP WILL NEVER BE EXACTLY LIKE ONE DEFINED.
    
    def position_to_dict(self):

        return {
            "direction" : self.direction,
            "open_time" : self.open_time,
            "entry_p" : self.entry_p,
            "pct_at_risk" : self.pct_risk,
            "capital_at_risk" : self.capital_at_risk,
            "spread_in_pips" : self.spread_in_pips,
            "pips_in_sl" : abs(self.entry_p-self.sl) / self.pip,
            "sl" : self.sl,
            "tp" : self.tp,
            "pips_in_tp" : abs(self.tp-self.entry_p) / self.pip,
            "RR" : self.risk_reward,
            "result" : self.result,
            "Loss_in_RR" : -1 if self.result == "SL" else self.risk_reward,
            "close_time" : self.close_time,
            "duration_in_candles" : self.duration_in_candles,
            "pnl" : self.pnl,
            "commission" : self.commission
        }

class RiskModel:

    def __init__(self,entry_p:float,lst_highs:list,lst_lows:list,tick_measurement:float):

        self.entry_p = entry_p
        self.lst_highs = lst_highs
        self.lst_lows = lst_lows
        self.tick_measurement = tick_measurement

        self.sl = None
        self.tp = None
    
    def get_sl(self,minimum_ticks_for_sl:float):

        lows_reversed = self.lst_lows.copy()
        lows_reversed.reverse()

        for low in lows_reversed:

            ticks_from_entry = (self.entry_p - low) / self.tick_measurement

            if ticks_from_entry >= minimum_ticks_for_sl :

                self.sl = low
                break
    
    def get_tp(self,minimum_risk_reward:float):

        if self.sl != None:

            highs_reversed = self.lst_highs.copy()
            highs_reversed.reverse()

            for high in highs_reversed:

                pips_in_sl = abs(self.entry_p - self.sl) / self.tick_measurement
                distance_from_entry = (high - self.entry_p) / self.tick_measurement
                if distance_from_entry >= minimum_risk_reward * pips_in_sl:

                    self.tp = high
                    break
                
    def build_trade_levels(self,minimum_ticks_for_sl:float,minimum_risk_reward:float):

        self.get_sl(minimum_ticks_for_sl)
        self.get_tp(minimum_risk_reward)
        if self.sl != None and self.tp != None:
            print(f"Entry_P:{self.entry_p},SL:{self.sl},TP:{self.tp}")


#PORTFOLIO COMPOSITION,FLOWS & DEALING WITH POSITIONS

@dataclass
class Portfolio:

    active_positions:list
    #EACH ELEMENT OF THE LIST WILL BE A DICT WITH entry_p,timestamp_entry,sl,tp,risk_to_reward,commission,max_loss,max_gain
    closed_trades:list
    #EACH ELEMENT OF THE LIST WILL BE A DICT WITH entry_p,timestamp_entry,sl,tp,risk_to_reward,result(sl,tp),gain(+)_loss(-),timestamp_exit
    disposable_balance:float
    lst_disposable_balance:list
    unrealized_balance:float
    lst_unrealized_balance:list
    equity_curve:float
    lst_equity_curve:list
    lst_pct_drawdown:list

    def new_trade_append(self,position:Position):

        self.active_positions.append(position)
    
    def update_portfolio_new_trade(self,position:Position):

        self.disposable_balance -= position.capital_at_risk
        self.unrealized_balance += position.value_added

    def update_portfolio(self,position:Position,last_candle:Candle):

        if position.result == None:

            self.unrealized_balance += position.value_added

        else:

            position.close_time = last_candle.timestamp
            self.active_positions.remove(position)
            if position.result == "TP":

                self.disposable_balance += position.capital_at_risk + position.pnl
                self.unrealized_balance += position.value_added #HERE VALUE ADDED HAS ALREADY THE COMMISSION
                self.equity_curve += position.pnl
                print(rf"Position closed at {position.close_time}, the result was {position.result} and the pnl from the position was {position.pnl}")
            
            else: #SL

                self.disposable_balance += position.capital_at_risk
                self.disposable_balance += position.pnl
                self.unrealized_balance += position.value_added #HERE VALUE ADDED HAS ALREADY THE COMMISSION
                self.equity_curve += position.pnl
                print(rf"Position closed at {position.close_time}, the result was {position.result} and the pnl from the position was {position.pnl}")
            
            self.closed_trades.append(position.position_to_dict())
        
    def balances_update(self):

        self.lst_disposable_balance.append(self.disposable_balance) #THIS CAN BE HERE IT WILL UPDATE AT EACH POSITION, WHICH AIN'T THE GOAL
        self.lst_unrealized_balance.append(self.unrealized_balance)
        self.lst_equity_curve.append(self.equity_curve)
        #Current_Drawdown
        max_val = max(self.lst_unrealized_balance)
        idx_max = self.lst_unrealized_balance.index(max_val)
        temp_lst_to_calculate_drawdown = self.lst_unrealized_balance[idx_max:].copy()
        min_val = min(temp_lst_to_calculate_drawdown)
        possible_drawdown_pct = min_val/max_val - 1
        self.lst_pct_drawdown.append(possible_drawdown_pct)


#CHECK MARKET HOURS FOR TREATMENT OF CANDLES AND THEIR TIMING

class MarketHoursOpen:

    def check_fx_market_open(self,next_expected_candle:datetime):

        friday_above_ten_pm = next_expected_candle.weekday() == 4 and next_expected_candle.hour >= 17
        saturday = next_expected_candle.weekday() == 5
        sunday_below_5_pm = next_expected_candle.weekday() == 6 and next_expected_candle.hour < 17

        if friday_above_ten_pm or saturday or sunday_below_5_pm:

                while next_expected_candle.weekday() != 6:

                    next_expected_candle += pd.Timedelta(days=1)
                
                next_expected_candle = datetime(
                    year = next_expected_candle.year,
                    month = next_expected_candle.month,
                    day = next_expected_candle.day,
                    hour = 17,
                    minute = 0
                )

        return next_expected_candle
    
    #def us equities and other markets.

#COORDINATION OF MULTIPLE TIMEFRAMES GIVEN THE STRATEGY USES MULTIPLE TIMEFRAMES

class MultiTimeframeEngine:

    def __init__(self,engines:dict,buffers:dict,timeframes:dict,last_htf_candle:dict,next_expected_open:dict,latest_setups:dict,structures_when_trade_is_entered:dict):

        self.engines = engines
        self.buffers = buffers
        self.timeframes = timeframes
        self.last_htf_candle = last_htf_candle
        self.latest_setups = latest_setups
        self.next_expected_open = next_expected_open
        self.structures_when_trade_is_entered = structures_when_trade_is_entered

        self.prev_setups_latest = latest_setups
        self.every_structure = structures_when_trade_is_entered.copy() #dict in the same way that I want
        self.every_candles_in_range_list = structures_when_trade_is_entered.copy() #dict in the same way that I want

        self.market_hours = MarketHoursOpen()
        
    def build_candle_htf(self,key): 

        #TIMESTAMP WILL ALWAYS BE DEFINED BY THE TRIGGER TO ALLIGN WITH TIME
        minutes_in_htf_candle = self.timeframes[key]['ratio']   
        timestamp = self.next_expected_open[key]

        n_candles_to_combine = len(self.buffers[key])

        if n_candles_to_combine == 0:

            #UNPRINTABLE
            #TO AVOID ANY CHANGE IN THE MARKET STRUCTURE PRINT THOSE CANDLES AS BEING EQUAL TO THE CLOSE OF THE PREVIOUS CANDLE
            return Candle(
                timestamp = timestamp,
                open = self.last_htf_candle[key].close,
                high = self.last_htf_candle[key].close,
                low = self.last_htf_candle[key].close,
                close = self.last_htf_candle[key].close,
                tick_volume = 0
            )

        else:

            #OPEN ASSUMES THE 1ST CANDLE IMPRINTED
            #CLOSE ASSUMES THE LAST CANDLE IMPRINTED
            open = self.buffers[key][0].open
            close = self.buffers[key][-1].close
            high = max(candle.high for candle in self.buffers[key])
            low = min(candle.low for candle in self.buffers[key])
            tick_volume = sum(candle.tick_volume for candle in self.buffers[key])

            return Candle(
                timestamp = timestamp,
                open = open,
                high = high,
                low = low,
                close = close,
                tick_volume = tick_volume
            )


    def on_m1_candle(self,candle:Candle):

        self.prev_setups_latest = deepcopy(self.latest_setups)

        #print("Treating m1 Data")

        smallest_tf = list(self.latest_setups.keys())[0]

        if smallest_tf == 'm1':

            # always update M1
            self.latest_setups[smallest_tf] = self.engines[smallest_tf].on_candle(candle) #THIS SENDS AN INITIAL SIGNAL WHICH IS A SETUP EVENT OR NONE
            self.every_structure[smallest_tf].append(deepcopy(self.engines[smallest_tf].context.structure_snapshot))
            self.every_candles_in_range_list[smallest_tf].append(deepcopy(self.engines[smallest_tf].structure.candles_in_range))
            self.engines[smallest_tf].structure.candles_m1_per_each_candle = 1

        for tf in self.buffers:

            minutes_on_tf = self.timeframes[tf]['ratio']
            self.engines[tf].structure.candles_m1_per_each_candle = minutes_on_tf

            if self.last_htf_candle[tf] is None:

                self.buffers[tf].append(candle)
                starting_ts = self.buffers[tf][0].timestamp
                alligned_minutes = (starting_ts.minute // minutes_on_tf) * minutes_on_tf
                starting_ts = starting_ts.replace(
                    minute=alligned_minutes,
                    second=0,
                    microsecond=0
                )
                timestamp_ending_the_candle = starting_ts + pd.Timedelta(minutes = minutes_on_tf - 1)

                if candle.timestamp == timestamp_ending_the_candle:

                    open = self.buffers[tf][0].open
                    close = self.buffers[tf][-1].close
                    high = max(candle.high for candle in self.buffers[tf])
                    low = min(candle.low for candle in self.buffers[tf])
                    tick_volume = sum(candle.tick_volume for candle in self.buffers[tf])

                    first_candle_htf = Candle(
                        timestamp = starting_ts,
                        open = open,
                        high = high,
                        low = low,
                        close = close,
                        tick_volume = tick_volume
                    )

                    self.last_htf_candle[tf] = first_candle_htf

                    #print(f"Treating {tf} Data")

                    self.latest_setups[tf] = self.engines[tf].on_candle(first_candle_htf)
                    self.buffers[tf].clear()
                    #1ST TIMESTAMP

                    self.next_expected_open[tf] = first_candle_htf.timestamp + pd.Timedelta(minutes = minutes_on_tf)
                    self.next_expected_open[tf] = self.market_hours.check_fx_market_open(self.next_expected_open[tf])
                    self.every_structure[tf].append(deepcopy(self.engines[tf].context.structure_snapshot))
                    self.every_candles_in_range_list[tf].append(deepcopy(self.engines[tf].structure.candles_in_range))
            
            else:

                timestamp_ending_the_candle = self.next_expected_open[tf] + pd.Timedelta(minutes = minutes_on_tf - 1)

                if candle.timestamp < timestamp_ending_the_candle:

                    self.buffers[tf].append(candle)

                else: 

                    self.buffers[tf].append(candle)

                    """# WERE USED TO CHECK WHICH CANDLES WERE INCLUDED IN EACH CANDLE"""

                    # print("Building", tf)

                    # for c in self.buffers[tf]:

                    #     if tf == "m5":
                        
                    #         print(c.timestamp)

                    htf_candle = self.build_candle_htf(tf)

                    self.next_expected_open[tf] = htf_candle.timestamp + pd.Timedelta(minutes = minutes_on_tf)

                    self.next_expected_open[tf] = self.market_hours.check_fx_market_open(self.next_expected_open[tf])

                    self.last_htf_candle[tf] = htf_candle

                    #print(f"Changing Struct on Candle of TF : {tf}")

                    self.latest_setups[tf] = self.engines[tf].on_candle(htf_candle) #THIS ALSO SENDS A SIGNAL IN HTFs WHICH IS A SETUP EVENT OR NONE

                    self.every_structure[tf].append(deepcopy(self.engines[tf].context.structure_snapshot))

                    self.every_candles_in_range_list[tf].append(deepcopy(self.engines[tf].structure.candles_in_range))

                    self.buffers[tf].clear()


#CREATION OF MARKET ORDERS, DEFINING SL & TP BASED OFF 'RiskModel'
#FILL PENDING ORDERS
#UPDATE POSITIONS BASED ON THEIR PRICE LEVEL AND THEIR RESPECTIVE SL & TP

#LATER IT COULD ALSO DO:
# apply spread
# apply slippage
# simulate execution latency

minimum_ticks_for_sl = float(input("Minimum Pips SL for each Trade: "))
minimum_risk_reward = float(input("Minimum Risk to Reward for each Trade: "))
minimum_minutes_between_market_orders = int(input("Minimum Minutes Between Consecutive but Different Creation of Market Orders: "))
minimum_minutes_between_last_order_fill = int(input("Minimum Minutes Between Consecutive but Different Fills of Market Orders: "))

class BrokerSimulator:

    def __init__(self,instrument,portfolio):

        self.instrument = instrument
        self.portfolio = portfolio
        
        self.pending_market_orders = []
    
    def create_market_order(self,candle:Candle):

        market_orders_not_empty = len(self.pending_market_orders) != 0

        if market_orders_not_empty:

            last_market_order = self.pending_market_orders[-1]
            seconds_since_emission_market_order = (candle.timestamp - last_market_order.timestamp).seconds
            if seconds_since_emission_market_order / 60 >= minimum_minutes_between_market_orders:

                order = MarketOrder(
                symbol="EURUSD",
                direction="BUY",
                timestamp=candle.timestamp,
                status="PENDING",
                fill_price=None,
                fill_timestamp=None
                )

                print(f"MarketOrder created at {order.timestamp}")

                return order      

        else:

            order = MarketOrder(
            symbol="EURUSD",
            direction="BUY",
            timestamp=candle.timestamp,
            status="PENDING",
            fill_price=None,
            fill_timestamp=None
            )

            print(f"MarketOrder created at {order.timestamp}")

            return order

    def define_sl_tp(self,candle:Candle,local_highs:list,local_lows:list):

        trade_levels_object = RiskModel(
            entry_p = candle.open,
            lst_highs = local_highs,
            lst_lows = local_lows,
            tick_measurement = 0.0001
        )

        #MINIMUM SL & MINIMUM RR
        trade_levels_object.build_trade_levels(minimum_ticks_for_sl,minimum_risk_reward) #THEN FIND A WAY TO INPUT BEFOREHAND MINIMUM SL AND MINIMUM_RR

        return trade_levels_object

    def fill_pending_orders(self,candle:Candle,local_highs:list,local_lows:list):

        market_orders_not_empty = len(self.pending_market_orders) != 0
        positions_exist = len(self.portfolio.active_positions) != 0

        if market_orders_not_empty:

            last_market_order = self.pending_market_orders[-1]

            if last_market_order.status == "FILLED" :

                print(last_market_order)

            seconds_since_emission_market_order = (candle.timestamp - last_market_order.timestamp).seconds

            if seconds_since_emission_market_order / 60 <= minimum_minutes_between_last_order_fill:

                if positions_exist:

                    last_position = self.portfolio.active_positions[-1]
                    entry_time = last_position.open_time

                    seconds_since_last_order = (candle.timestamp - entry_time).seconds

                    if seconds_since_last_order / 60 <= minimum_minutes_between_last_order_fill:

                        last_market_order.status = "NOT FILLED, MARKET ORDER OF THIS SIGNAL ALREADY EXISTS"

                    else:

                        trade_levels = self.define_sl_tp(candle,local_highs,local_lows)

                        if trade_levels.sl != None and trade_levels.tp != None:

                            position = Position(
                                direction="BUY",
                                entry_p = trade_levels.entry_p,
                                sl= trade_levels.sl,
                                tp = trade_levels.tp,
                                pct_risk = 0.01,
                                spread_in_pips = 1.2,
                                open_time = candle.timestamp
                            )

                            #PCT_COMMISSION,CANDLE & AVAILABLE BALANCE
                            position.build_initial_trade_metadata(0.1,candle,self.portfolio.disposable_balance)

                            self.portfolio.new_trade_append(position)
                            self.portfolio.update_portfolio_new_trade(position)
                            print(f"[{candle.timestamp}] ",f"NEW POSITION BUY @ {position.entry_p}")

                            last_market_order.status = "FILLED"
                            last_market_order.fill_price = self.portfolio.active_positions[-1].entry_p
                            last_market_order.fill_timestamp = self.portfolio.active_positions[-1].open_time
                        
                        else:

                            last_market_order.status = "NOT FILLED"
                else:

                    trade_levels = self.define_sl_tp(candle,local_highs,local_lows)

                    if trade_levels.sl != None and trade_levels.tp != None:

                        position = Position(
                            direction="BUY",
                            entry_p = trade_levels.entry_p,
                            sl= trade_levels.sl,
                            tp = trade_levels.tp,
                            pct_risk = 0.01,
                            spread_in_pips = 1.2,
                            open_time = candle.timestamp
                        )

                        #PCT_COMMISSION,CANDLE & AVAILABLE BALANCE
                        position.build_initial_trade_metadata(0.1,candle,self.portfolio.disposable_balance)

                        self.portfolio.new_trade_append(position)
                        self.portfolio.update_portfolio_new_trade(position)
                        print(f"[{candle.timestamp}] ",f"NEW POSITION BUY @ {position.entry_p}")

                        last_market_order.status = "FILLED"
                        last_market_order.fill_price = self.portfolio.active_positions[-1].entry_p
                        last_market_order.fill_timestamp = self.portfolio.active_positions[-1].open_time
                    
                    else:

                        last_market_order.status = "NOT FILLED"

            else:

                last_market_order.status = "NOT FILLED"

    def check_tp_hit(self,position:Position,last_candle:Candle):

        #TRADE WILL COME FROM PORTFOLIO
        last_candle_low = last_candle.low
        last_candle_high = last_candle.high
        current_timestamp = last_candle.timestamp
        tp_is_hit = last_candle_high > position.tp if position.direction == "BUY" else last_candle_low < position.tp
        sl_is_hit = last_candle_low <= position.sl if position.direction == "BUY" else last_candle_high >= position.sl
        sl_not_hit = sl_is_hit == False

        if tp_is_hit and sl_not_hit: #CASES WHERE BOTH ARE IT WILL BE SEEN AS LOSSES

            position.result = "TP"
            position.close_time = current_timestamp

    def check_sl_hit(self,position:Position,last_candle:Candle):

        #TRADE WILL COME FROM PORTFOLIO
        last_candle_low = last_candle.low
        last_candle_high = last_candle.high
        current_timestamp = last_candle.timestamp
        sl_is_hit = last_candle_low <= position.sl if position.direction == "BUY" else last_candle_high >= position.sl

        if sl_is_hit:

            position.result = "SL"
            position.close_time = current_timestamp

    def calculate_change_pnl(self,position:Position,last_candle:Candle):

        #TRADE WILL COME FROM PORTFOLIO
        spread_deviation = (position.pip * position.spread_in_pips) / 2 
        last_candle_close = last_candle.close
        position.duration_in_candles += 1
        #candle_close_spread_adjusted = last_candle_close - spread_deviation if position.direction == "BUY" else last_candle_close + spread_deviation

        if position.result == "TP":

            price_change = position.tp - position.current_price if position.direction == "BUY" else -(position.tp - position.current_price)
            change_in_pips = price_change / position.pip
            pct_change_in_total_pips_sl = change_in_pips / position.pips_sl
            pnl_change = pct_change_in_total_pips_sl * position.capital_at_risk
            position.current_price = last_candle_close #candle_close_spread_adjusted
            position.pnl = position.pnl + pnl_change - position.commission
            position.value_added = pnl_change - position.commission
            

        elif position.result == "SL":

            price_change = position.sl - position.current_price if position.direction == "BUY" else -(position.sl - position.current_price)
            change_in_pips = price_change / position.pip
            pct_change_in_total_pips_sl = change_in_pips / position.pips_sl
            pnl_change = pct_change_in_total_pips_sl * position.capital_at_risk
            position.current_price = last_candle_close #candle_close_spread_adjusted
            position.pnl = position.pnl + pnl_change - position.commission
            position.value_added = pnl_change - position.commission
        
        else: #NONE

            price_change = last_candle_close - position.current_price if position.direction == "BUY" else -(last_candle_close - position.current_price)
            change_in_pips = price_change / position.pip
            pct_change_in_total_pips_sl = change_in_pips / position.pips_sl
            pnl_change = pct_change_in_total_pips_sl * position.capital_at_risk
            position.current_price = last_candle_close #candle_close_spread_adjusted
            position.pnl = position.pnl + pnl_change
            position.value_added = pnl_change

    def update_position(self,position:Position,last_candle:Candle):

        self.check_tp_hit(position,last_candle)
        self.check_sl_hit(position,last_candle)
        self.calculate_change_pnl(position,last_candle)

#TURNING THE LST OF CANDLES INTO DF
#PUTTING CANDLES FROM DF INTO VISUAL USING PLOTLY
#HISTORICAL LISTS OF BALANCES INTO DF
#HISTOGRAM OF ALL CANDLES RETURNS
#CLOSED TRADES STATS IN DF

class GraphicHelpers:

    def lst_timeframes_to_dataframe(self,lst_with_candles_in_a_timeframe:list):

        df_combined = pd.DataFrame(columns=["Date","Open","High","Low","Close","Tick_Volume"])

        for candle in lst_with_candles_in_a_timeframe:

            c_timestamp = candle["current_candle"]["current_candle_ts"]
            c_open = candle["current_candle"]["current_candle_open"]
            c_high = candle["current_candle"]["current_candle_high"]
            c_low = candle["current_candle"]["current_candle_low"]
            c_close = candle["current_candle"]["current_candle_close"]
            c_tick_vol = candle["current_candle"]["current_candle_tick_vol"]

            row = pd.DataFrame([{
                "Date" : c_timestamp,
                "Open" : c_open,
                "High" : c_high,
                "Low" : c_low,
                "Close" : c_close,
                "Tick_Volume" : c_tick_vol
            }])

            df_combined = pd.concat([df_combined,row],axis=0,ignore_index=True)

        return df_combined

    def ohlc_df_to_visual_candles(self,df_to_print: pd.DataFrame,structure_snapshot:dict):

        active_range = structure_snapshot["active_range"]
        active_range_direction = active_range.direction
        #INIT TIMESTAMP CONCERNS THE CANDLE BEFORE THE FVG
        dict_fvg = structure_snapshot["fv_gaps"] #timestamps as keys and then as list the point of the fvg before and after fvg
        newest_ts = structure_snapshot["current_candle"]["current_candle_ts"]

        list_start_fvg = []
        list_end_fvg = []
        fvg = []
        fvg_ts = []

        for key in dict_fvg:

            fvg_temp = []
            fvg_ts_temp = []

            (before_ts, before_price), (after_ts, after_price) = dict_fvg[key].items()

            fvg_temp.append(before_price)
            fvg_temp.append(after_price)
            fvg.append(fvg_temp)

            fvg_ts_temp.append(before_ts)
            fvg_ts_temp.append(after_ts)
            fvg_ts.append(fvg_ts_temp)

        """RECEIVES THE RANGE STAT TO BE PRINTED"""
        tstamp_high = active_range.timestamp_high
        tstamp_low = active_range.timestamp_low

        oldest_value = tstamp_high if tstamp_high <= tstamp_low else tstamp_low
        recent_value = tstamp_high if tstamp_high > tstamp_low else tstamp_low

        print(f"Recent_Value_ts : {recent_value} & Oldest_Val_ts : {oldest_value} ")

        list_local_highs = []
        list_local_highs_ts = []
        list_local_lows = []
        list_local_lows_ts = []

        for i in range(len(structure_snapshot["local_highs"])):

            if newest_ts >= structure_snapshot["local_highs_ts"][i] >= oldest_value:

                list_local_highs.append(structure_snapshot["local_highs"][i])
                list_local_highs_ts.append(structure_snapshot["local_highs_ts"][i])

        for i in range(len(structure_snapshot["local_lows"])):

            if newest_ts >= structure_snapshot["local_lows_ts"][i] >= oldest_value:

                list_local_lows.append(structure_snapshot["local_lows"][i])
                list_local_lows_ts.append(structure_snapshot["local_lows_ts"][i])

        
        #print(dict_fvg,list_start_fvg,list_start_fvg_ts,list_local_lows,list_local_lows_ts)

        idx_first_extreme = df_to_print[df_to_print['Date'] == oldest_value].index[0]
        idx_last_extreme = df_to_print[df_to_print['Date'] == recent_value].index[0]
        most_recent_candle_idx = df_to_print[df_to_print['Date'] == newest_ts].index[0]

        #return idx_first_extreme,oldest_value,idx_last_extreme,recent_value,list_local_highs,list_local_lows

        df_to_print = df_to_print.loc[idx_first_extreme-30:most_recent_candle_idx,['Date', 'Open', 'High', 'Low', 'Close']]
        #df_to_print["Local_Highs"] = df_to_print["High"].isin(list_local_highs) & df_to_print['Date'].isin(list_local_highs_ts)
        #df_to_print["Local_Lows"] = df_to_print["Low"].isin(list_local_lows) & df_to_print['Date'].isin(list_local_lows_ts)

        local_high_pairs = set(
            zip(list_local_highs_ts, list_local_highs)
        )

        df_to_print["Local_Highs"] = df_to_print.apply(
            lambda row:
                (row["Date"], row["High"]) in local_high_pairs,
            axis=1
        )

        local_low_pairs = set(
            zip(list_local_lows_ts, list_local_lows)
        )

        df_to_print["Local_Lows"] = df_to_print.apply(
            lambda row:
                (row["Date"], row["Low"]) in local_low_pairs,
            axis=1
        )

        start_fvg = set(
            zip([lst[0] for lst in fvg_ts], [lst[0] for lst in fvg])
        )

        df_to_print["Start_fvg"] = df_to_print.apply(
            lambda row:
                (row["Date"], row["High"]) in start_fvg if active_range_direction == "Low-High" else (row["Date"], row["Low"]) in start_fvg,
            axis=1
        )

        end_fvg = set(
            zip([lst[1] for lst in fvg_ts], [lst[1] for lst in fvg])
        )

        df_to_print["End_fvg"] = df_to_print.apply(
            lambda row:
                (row["Date"], row["Low"]) in end_fvg if active_range_direction == "Low-High" else (row["Date"], row["High"]) in end_fvg,
            axis=1
        )
        
        print(local_high_pairs)
        print(list_local_highs_ts)
        print(local_low_pairs)
        print(list_local_lows_ts)
        print(f"list of the starts of fvgs : {start_fvg}")
        print(f"list of the ends of fvgs : {end_fvg}")
        print(active_range)
        print(fvg)
        print(fvg_ts)

        #print(df_to_print.at[df_to_print.loc[df_to_print["Date"] == datetime(2012,4,16,7,45)].index[0],"High"],fvg[0][1],df_to_print.at[df_to_print.loc[df_to_print["Date"] == datetime(2012,4,16,7,45)].index[0],"High"] == fvg[0][1] )

        #print(df_to_print.loc[df_to_print['Start_fvg'] == True])
        #print(df_to_print.loc[df_to_print['End_fvg'] == True])

        # Create the candlestick chart
        fig = go.Figure(data=[
            go.Candlestick(
                x=df_to_print['Date'],
                open=df_to_print['Open'],
                high=df_to_print['High'],
                low=df_to_print['Low'],
                close=df_to_print['Close'],
                increasing_line_color='blue',    # border color up candles
                decreasing_line_color='black',      # border color down candles
                increasing_fillcolor='blue',    # fill color up candles
                decreasing_fillcolor='black',           # fill color down candles
            )
        ])

        fig.update_layout(
            title='Interactive Candlestick Chart',
            xaxis_title='Date',
            yaxis_title='Price',
            xaxis_rangeslider_visible=True,  # allows zooming and sliding
            template='plotly_white',
            width=1500,
            height=900,
            margin=dict(l=80, r=40, t=80, b=60),

        )

        # Remove Non-FX Hours

        hidden = df_to_print.loc[
            (
                (df_to_print["Date"].dt.weekday == 4) & (df_to_print["Date"].dt.hour >= 17)
            )
            |
            (df_to_print["Date"].dt.weekday == 5)
            |
            (
                (df_to_print["Date"].dt.weekday == 6) & (df_to_print["Date"].dt.hour < 17)
            ),
            "Date"
        ]

        fig.update_xaxes(
            rangebreaks=[
                dict(values=hidden)
            ]
        )

        # Remove gridlines

        fig.update_yaxes(
            showgrid=False           
        )

        """
        df_to_print.loc[df_to_print['Range_Status']['Discount'] == True]
        """

        #Adding Annotations
        list_local_highs = df_to_print.loc[df_to_print['Local_Highs'] == True].index.to_list()
        list_local_lows = df_to_print.loc[df_to_print['Local_Lows'] == True].index.to_list()
        list_start_fvg = df_to_print.loc[df_to_print['Start_fvg'] == True].index.to_list()
        list_end_fvg = df_to_print.loc[df_to_print['End_fvg'] == True].index.to_list()
        print("Printing Annotations:")
        print(f"list_local_highs : {list_local_highs},list_local_lows : {list_local_lows},list_start_fvg : {list_start_fvg}, list_end_fvg : {list_end_fvg}")
        # list_premium_areas = df_to_print.loc[df_to_print['Premium_Area'] == True].index.to_list()
        # list_discount_areas = df_to_print.loc[df_to_print['Discount_Area'] == True].index.to_list()
        # last_index_df_to_print = df_to_print.index[-1]
        # ind_day_first_extreme = df_to_print.at[last_index_df_to_print,'Active_Range_Stats'][2] 
        # ind_day_last_extreme = df_to_print.at[last_index_df_to_print,'Active_Range_Stats'][3] 
        #Annotations_Default
        base_style_local_low = dict(
            showarrow=True, 
            arrowhead=2, 
            ax=0, 
            ay=30, 
            font=dict(color='white',size=12), 
            bgcolor='rgba(0,0,0,0.5)'
        )
        base_style_local_high = dict(
            showarrow=True, 
            arrowhead=2, 
            ax=0, 
            ay=-30, 
            font=dict(color='white',size=12), 
            bgcolor='rgba(0,0,0,0.5)'
        )
        base_style_fvg = dict(
            showarrow=True, 
            arrowhead=2, 
            ax=-50, 
            ay=-30, 
            font=dict(color='white',size=12), 
            bgcolor='rgba(0,0,0,0.5)'
        )
        
        for index in list_local_highs:

            fig.add_annotation(
                x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'High'],
                text='Local_High',
                **base_style_local_high
            )
        for index in list_local_lows:

            fig.add_annotation(
                x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'Low'],
                text='Local_Low',
                **base_style_local_low
            )
        
        for index in list_start_fvg:

            if active_range_direction == "Low-High":

                fig.add_annotation(
                    x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'High'],
                    text='Start_Ext_FVG',
                    **base_style_fvg
                )

            else:

                fig.add_annotation(
                    x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'Low'],
                    text='Start_Ext_FVG',
                    **base_style_fvg
                )
            
        for index in list_end_fvg:

            if active_range_direction == "Low-High":
                
                fig.add_annotation(
                    x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'Low'],
                    text='End_Ext_FVG',
                    **base_style_fvg
                )

            else:

                fig.add_annotation(
                    x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'High'],
                    text='End_Ext_FVG',
                    **base_style_fvg
                )

        """THE MAIN PROBLEM IS THAT THE CANDLES ARE ADVANCED BY ONE CANDLE"""

        #For Premium Areas and Discounted Areas
        
        # base_style_discount_areas = dict(
        #     showarrow=True, 
        #     arrowhead=2, 
        #     ax=0, 
        #     ay=50, 
        #     font=dict(color='red',size=12), 
        #     bgcolor='rgba(0,0,0,5)'
        # )
        # base_style_premium_areas = dict(
        #     showarrow=True, 
        #     arrowhead=2, 
        #     ax=0, 
        #     ay=-50, 
        #     font=dict(color='red',size=12), 
        #     bgcolor='rgba(0,0,0,5)'
        # )
        # for index in list_premium_areas:

        #     fig.add_annotation(
        #         x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'High'],
        #         text='Prem_Area',
        #         **base_style_premium_areas
        #     )
        # for index in list_discount_areas:
            
        #     fig.add_annotation(
        #         x=df_to_print.loc[index,'Date'], y=df_to_print.loc[index,'Low'],
        #         text='Disc_Area',
        #         **base_style_discount_areas
        #     )
        
        # #For The values of a given Range

        # #Settings

        base_style_range_extremes_highs = dict(
            showarrow=True, 
            arrowhead=2, 
            ax=0, 
            ay=-100, 
            font=dict(color='white',size=12), 
            bgcolor='rgba(0,0,0,5)'
        )

        base_style_range_extremes_lows = dict(
            showarrow=True, 
            arrowhead=2, 
            ax=0, 
            ay=100, 
            font=dict(color='white',size=12), 
            bgcolor='rgba(0,0,0,5)'
        )
        
        if active_range_direction == 'Low-High':

            #Add first_extreme_range
            fig.add_annotation(
                x=df_to_print.at[idx_first_extreme,'Date'], y = df_to_print.at[idx_first_extreme,'Low'],
                text = 'Range_Start',
                **base_style_range_extremes_lows
                
            )

            #Add last_extreme_range
            fig.add_annotation(
                x=df_to_print.at[idx_last_extreme,'Date'], y = df_to_print.at[idx_last_extreme,'High'],
                text = 'Range_End',
                **base_style_range_extremes_highs

            )
        
        else: #'High-Low'

            #Add first_extreme_range
            fig.add_annotation(
                x=df_to_print.at[idx_first_extreme,'Date'], y =df_to_print.at[idx_first_extreme,'High'],
                text = 'Range_Start',
                **base_style_range_extremes_highs

            )

            #Add last_extreme_range
            fig.add_annotation(
                x=df_to_print.at[idx_last_extreme,'Date'], y =df_to_print.at[idx_last_extreme,'Low'],
                text = 'Range_End',
                **base_style_range_extremes_lows

            )

        return fig.show()
        
    def lst_balances_to_candle(self,lst_disp_balance:list,lst_unrealized_balance:list,lst_equity_curve:list,lst_pct_drawdown:list):

        df_combined = pd.DataFrame(columns=["Disposable_Balance","Unrealized_Balance","Equity_Curve"])
        df_combined["Disposable_Balance"] = lst_disp_balance
        df_combined["Unrealized_Balance"] = lst_unrealized_balance
        df_combined["Returns_p/Candle"] = df_combined["Unrealized_Balance"].pct_change()
        df_combined["Equity_Curve"] = lst_equity_curve
        df_combined["Pct_Drawdown"] = lst_pct_drawdown

        return df_combined

    def histogram_of_returns(self,lst_disp_balance:list,lst_unrealized_balance:list,lst_equity_curve:list):

        df_balances = self.lst_balances_to_candle(lst_disp_balance,lst_unrealized_balance,lst_equity_curve)
        returns = df_balances["Returns_p/Candle"]

        fig = go.Figure(
            data=[
                go.Histogram(
                    x=returns,
                    histnorm="probability",
                    #nbinsx=50
                )
            ]
        )

        fig.show()

    def closed_trades_in_df(self,lst_closed_trades:list):

        dict_all_trades = {}
        trade_keys = lst_closed_trades[0].keys()
        for key in trade_keys:

            dict_all_trades[key] = list()
        
        for closed_position in lst_closed_trades:

            for key in closed_position:

                dict_all_trades[key].append(closed_position[key])
        
        df_closed_trades = pd.DataFrame.from_dict(dict_all_trades)

        return df_closed_trades

#SOME OF THE METRICS USED TO ASSESS THE STRATEGIES

class Strategy_Metrics: #1st You need to Transform Data using GraphicHelpers Class

    def __init__(self,df_balances:pd.DataFrame,closed_trades_lst:list):

        self.df = df_balances
        self.lst_close_trades = closed_trades_lst

    def period_return(self):

        df = self.df
        initial_capital = df["Unrealized_Balance"][0]
        final_capital = df["Unrealized_Balance"][-1]

        return (final_capital/initial_capital) - 1

    def cagr_candle_return(self):

        df = self.df
        period_return = self.period_return()
        n_candles = len(df) - 1
        initial_capital = df["Unrealized_Balance"][0]
        final_capital = df["Unrealized_Balance"][-1]
        cagr = ((final_capital/initial_capital)**(1/n_candles)) - 1

        return cagr

    def avg_candle_stdev(self):

        df = self.df
        series_returns = df["Returns_p/Candle"]

        return series_returns.std()

    def sharpe_of_period(self,risk_free):

        df = self.df
        n_annual = len(df) - 1

        return (self.cagr_candle_return() * n_annual - risk_free) / (self.avg_candle_stdev() * np.sqrt(n_annual))

    def calmar_of_period(self,risk_free):

        df = self.df
        series_drawdown = df["Pct_Drawdown"]
        n_annual = len(df) - 1

        return (self.cagr_candle_return() * n_annual - risk_free) / abs(min(series_drawdown))  #Min because drawdown is always negative or 0

    def sortino_of_period(self,risk_free):

        #Only_Negative_Returns
        df = self.df
        n_annual = len(df) - 1

        serie_negative_ret = df[df['Returns_p/Candle'] < 0]['Returns_p/Candle']
        avg_dev_series = sum([pow(ret,2) for ret in serie_negative_ret]) / n_annual
        stdev_annual = np.sqrt(avg_dev_series)

        #Denominator Sortino

        avg_annual_less_rf = self.cagr_candle_return() * n_annual - risk_free

        #Sortino

        sortino = avg_annual_less_rf / stdev_annual

        return sortino

    def win_losses_stats(self,risk_free_rate:float) -> dict: #Give the last index of the DF with all closed trades, returns a list with win_rate,avg_duration_days,profit_factor,expected_value_per_trade

        dict_stats = {}
        winners = sum([1 for trade in self.closed_trades_lst if trade['result'] == 'TP'])
        losses = sum([1 for trade in self.closed_trades_lst if trade['result'] == 'SL'])
        win_rate = winners / (winners+losses) if winners+losses > 0 else 0
        dict_stats["Win_Rate"] = win_rate
        #expected_gain = rr*win_rate  #centered on unit
        #expected_loss = 1*(1-win_rate) #centered on unit
        #expected_val_per_trade = expected_gain - expected_loss
        avg_duration_candles = np.mean([trade["duration_in_candles"] for trade in self.closed_trades_lst])
        dict_stats["Average_Candle_Duration"] = avg_duration_candles
        total_profits = sum([trade['pnl'] for trade in self.closed_trades_lst if trade['result'] == 'TP'])
        dict_stats["Total_Profits"] = total_profits
        total_losses = sum([trade['pnl'] for trade in self.closed_trades_lst if trade['result'] == 'SL'])
        dict_stats["Total_Losses"] = total_losses
        profit_factor = total_profits / total_losses if total_losses > 0 else 0
        dict_stats["Profit_Factor"] = profit_factor
        expected_value_per_trade = (total_profits - total_losses) / len(self.closed_trades_lst)
        dict_stats["Expected_Value_p/Trade"] = expected_value_per_trade
        dict_stats["Period_CAGR"] = self.cagr_candle_return()
        dict_stats["Sharpe_Ratio"] = self.sharpe_of_period(risk_free_rate)
        dict_stats["Sortino_Ratio"] = self.sortino_of_period(risk_free_rate)
        dict_stats["Calmar_Ratio"] = self.calmar_of_period(risk_free_rate)

        
        return dict_stats

#EXECUTION DYNAMIC TO RUN THE BACKTEST CANDLE BY CANDLE

class ExecutionEngine:

    def __init__(self,multi_tf_engine:MultiTimeframeEngine,broker:BrokerSimulator):

        self.multi_tf_engine = multi_tf_engine
        self.broker = broker

        self.confluence_engine = ConfluenceEngine(multi_tf_engine.latest_setups.copy())
        self.tf_keys = list(self.multi_tf_engine.engines.keys())
        self.tf_len = len(self.tf_keys)
        self.small_tf = self.tf_keys[0]
        
    def on_candle(self,candle:Candle):

        struct_snapshot = self.multi_tf_engine.engines[self.small_tf].context.structure_snapshot

        if struct_snapshot is None:

            self.multi_tf_engine.on_m1_candle(candle) #UPDATES EVERYTHING
            act_range = self.multi_tf_engine.engines[self.small_tf].context.structure_snapshot["active_range"]
            #print(act_range.direction,act_range.timestamp_low if act_range.direction == "Low-High" else act_range.timestamp_high,act_range.timestamp_high if act_range.direction == "Low-High" else act_range.timestamp_low,candle.timestamp)

        else:
            
            local_highs = self.multi_tf_engine.engines[self.small_tf].context.structure_snapshot['local_highs']
            local_lows = self.multi_tf_engine.engines[self.small_tf].context.structure_snapshot['local_lows']

            self.broker.fill_pending_orders(candle,local_highs,local_lows)

            for position in self.broker.portfolio.active_positions.copy(): #USE A COPY BECAUSE SOME TRADES WILL BE REMOVED

                self.broker.update_position(position,candle)
                self.broker.portfolio.update_portfolio(position,candle)
            
            self.broker.portfolio.balances_update()

            self.multi_tf_engine.on_m1_candle(candle) #UPDATES EVERYTHING

            if len(self.broker.pending_market_orders) != 0:

                last_market_order = self.broker.pending_market_orders[-1]
                if last_market_order.status == "FILLED":
                    for tf in self.tf_keys:

                        self.multi_tf_engine.structures_when_trade_is_entered[tf].append(deepcopy(self.multi_tf_engine.engines[tf].context.structure_snapshot))
                        # self.multi_tf_engine.structures_when_trade_is_entered['m5'].append(deepcopy(self.multi_tf_engine.engines['m5'].context.structure_snapshot))
                        # self.multi_tf_engine.structures_when_trade_is_entered['m15'].append(deepcopy(self.multi_tf_engine.engines['m15'].context.structure_snapshot))
                        #WHENEVER ONE ENTERS A TRADE, A NEW ONE CAN ONLY BE ENTERED IF ALL THE CONDITIONS ARE MET BUT THE TIMEFRAME IN THE MIDDLE
                        #CHANGED ITS CONDITIONS.

            """AT THIS STAGE THIS WORKS BECAUSE ONE IS ONLY BUYING BUT IF ONE STARTS BUYING AND SELLING, ONE WILL NEED TO ACCOUNT FOR THAT"""
            intent = self.confluence_engine.update(self.multi_tf_engine.prev_setups_latest,self.multi_tf_engine.latest_setups)

            if intent:
                mkt_order = self.broker.create_market_order(candle)
                if mkt_order != None:
                    self.broker.pending_market_orders.append(mkt_order)
                for tf in self.multi_tf_engine.latest_setups:
                    self.multi_tf_engine.latest_setups[tf] = None #TO AVOID CONTINOUS CREATION OF TRADES
                
                #print(self.multi_tf_engine.engines['m1'].context.structure_snapshot)
    
#MEMORYLESS AND 'ATRIBULESS' CLASS RESPONSIBLE FOR RUNNING THE THE BACKTEST 

class BacktestRunner:

    def run_backtest(self,execution_machine:ExecutionEngine,lst_hist_candles:list):

        for candle in lst_hist_candles:

            execution_machine.on_candle(candle)

