import os
import pandas as pd, numpy as np

PAGE_SIZE = 10
ID_HEADER = 'id'
WELL_NAME_HEADER = "Well Name"
WELL_TYPE_HEADER = "Well Type"
WELL_CONTROL_HEADER = "Well Control"
LOWER_BOUND_HEADER = "Lower Bound"
UPPER_BOUND_HEADER = "Upper Bound"
TIME_HEADER = "Time"
VALUE_HEADER = "Value"
VARIABLE_NAME_ORIGINAL = "Variable Name - Original"
DEFAULT_SCENARIO_COL = "Default Scenario"
VARIABLE_NAME_HEADER = "Variable Name"
FIXED_HEADERS = [ID_HEADER, WELL_NAME_HEADER, WELL_TYPE_HEADER, WELL_CONTROL_HEADER,
                 LOWER_BOUND_HEADER, UPPER_BOUND_HEADER, TIME_HEADER, VARIABLE_NAME_ORIGINAL]


def well_agg_main_table(x: pd.Series):
    all_equal = all(abs(item - x.iloc[0])<1e-10 for item in x.values)
    if all_equal: return x.iloc[0]
    else: return "varying"


def get_scenario_cols(df):
    scenario_cols = []
    for col in df.columns:
        if col not in FIXED_HEADERS and not col.startswith(VARIABLE_NAME_HEADER):
            scenario_cols.append(col)
    return scenario_cols


def get_avg_df(df):

    """ Return the data for the main table """

    scenario_columns = get_scenario_cols(df)
    cols = [WELL_NAME_HEADER, WELL_TYPE_HEADER] + scenario_columns

    df_main = df[cols].groupby(by=[WELL_NAME_HEADER,WELL_TYPE_HEADER])[scenario_columns].agg(func=well_agg_main_table).reset_index()

    df_main[ID_HEADER] = df_main[WELL_NAME_HEADER]
    df_main.set_index(ID_HEADER, inplace=True, drop=False)
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