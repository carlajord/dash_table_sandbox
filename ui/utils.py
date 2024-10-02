import os
import pandas as pd, numpy as np

PAGE_SIZE = 10
WELL_NAME_HEADER = "Well Name"
WELL_TYPE_HEADER = "Well Type"
WELL_CONTROL_HEADER = "Well Control"
LOWER_BOUND_HEADER = "LowerBound"
UPPER_BOUND_HEADER = "UpperBound"
TIME_HEADER = "Time"
VALUE_HEADER = "Value"
FIXED_HEADERS = [WELL_NAME_HEADER, WELL_TYPE_HEADER, WELL_CONTROL_HEADER,
                 LOWER_BOUND_HEADER, UPPER_BOUND_HEADER, TIME_HEADER]

def round_scenario_columns(df):
    temp_dict = {}
    [temp_dict.update({c:1}) for c in df.columns if 'Scenario' in c]
    df = df.round(temp_dict)
    return df

def well_agg_main_table(x: pd.Series):
    all_equal = all((item - x.iloc[0])<1e-10 for item in x.values)
    if all_equal: return x.iloc[0]
    else: return "varying"

def get_scenario_cols(df):
    return [col for col in df.columns if col not in FIXED_HEADERS]

def get_avg_df(df):

    """ Return the data for the main table """
    scenario_columns = get_scenario_cols(df)
    cols = [WELL_NAME_HEADER] + scenario_columns

    df_main = df[cols].groupby(by=WELL_NAME_HEADER).agg(func=well_agg_main_table).reset_index()

    df_main['id'] = df_main[WELL_NAME_HEADER]
    df_main.set_index('id', inplace=True, drop=False)
    return df_main

def make_table_conditional_formatting(df_cols):

    scenario_cols = get_scenario_cols(df_cols)

    condition = [
        {
            'if': {
                'state': 'active'  # 'active' | 'selected'
            },
            'backgroundColor': 'rgba(0, 116, 217, 0.3)',
            'border': '1px solid rgb(0, 116, 217)'
        }
    ]

    cond = [{
        'if': {
            'column_id': c
        },
        'color':'grey'
    } for c in scenario_cols]

    condition.extend(cond)

    return condition
