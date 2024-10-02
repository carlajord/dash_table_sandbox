import os
import pandas as pd

from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc

def round_scenario_columns(df):
    temp_dict = {}
    [temp_dict.update({c:1}) for c in df.columns if 'Scenario' in c]
    df = df.round(temp_dict)
    return df

def get_avg_df(df):
    df_avg = df.groupby(by='Well').aggregate(func='mean').reset_index().drop(columns=['Time'])
    df_avg['id'] = df_avg['Well']
    df_avg.set_index('id', inplace=True, drop=False)
    return df_avg

def make_modal():
    modal = dbc.Modal([
                dbc.ModalBody([
                    dbc.Row(html.P("Enter value to overwrite control for all time steps.")),
                    dbc.Row(dbc.InputGroup(children=[dbc.InputGroupText("Control Value:"),
                                                        dbc.Input(id="control-input")],
                                            className="mb-3")),
                    ]),
                dbc.ModalFooter([
                    dbc.Col("", width=4),
                    dbc.Col(dbc.Button("Confirm", id="confirm", n_clicks=0)),
                    dbc.Col(dbc.Button("Cancel", id="cancel", n_clicks=0))
                    ]
                ),
            ],
    id="modal",
    is_open=False,
    )
    return modal

def make_table_conditional_formatting(cols):
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
    } for c in cols if c.startswith('Scenario')]

    condition.extend(cond)

    return condition
