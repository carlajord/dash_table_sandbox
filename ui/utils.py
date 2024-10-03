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

def well_agg_main_table(x: pd.Series):
    all_equal = all(abs(item - x.iloc[0])<1e-10 for item in x.values)
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

    # changes the color of the active cell in the main table to blue
    condition = [
        {
            'if': {
                'state': 'active'
            },
            'backgroundColor': 'rgba(0, 116, 217, 0.3)',
            'border': '1px solid rgb(0, 116, 217)'
        }
    ]

    # changes the color of the numbers in the main table to grey
    cond = [{
        'if': {
            'column_id': c
        },
        'color':'grey'
    } for c in scenario_cols]

    condition.extend(cond)

    return condition
