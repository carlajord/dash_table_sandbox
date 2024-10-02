
import os, sys
import pandas as pd, numpy as np

from dash import Dash, dcc, html, dash_table
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc

from ui.utils import (round_scenario_columns, get_avg_df,
                      make_modal, make_table_conditional_formatting)


DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
UI_PATH = os.path.join(os.path.dirname(__file__), 'ui')

KEY = 'Well'
PAGE_SIZE = 5
OPEN_EYE = '<i class="fa fa-eye"></i>'
CLOSED_EYE = '<i class="fa fa-eye-slash"></i>'
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        FONT_AWESOME
    ],
    suppress_callback_exceptions=True
)

df_init = pd.read_csv(os.path.join(DATA_PATH,'random_data.csv'))
state_dict = {'df': df_init.to_dict(),
              'active_well': None,
              'active_scenario': None}

layout = dbc.Container(
    id='main-layout',
    children=[
        dbc.Row(html.Br()),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Scenario Control per Well"),
                dbc.CardBody([
                    dbc.Row([html.P("Click on a well scenario to edit controls \
                                    for each time step.")]),
                    dbc.Row([dash_table.DataTable(
                                id='datatable-avg',
                                page_size=PAGE_SIZE,
                                style_data_conditional=make_table_conditional_formatting(df_init.columns)
                            )]),
                        ]),
                    ]),
                width=8),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Scenario Control per Time Step"),
                dbc.CardBody([
                    dbc.Row([dbc.Col(html.P("Enter control value for each time \
                                            step or select 'Update All' to enter \
                                            constant value."),width=8),
                             dbc.Col([dbc.Button("Update All",
                                                 id='update-all',
                                                color="primary",
                                                className="mt-auto",
                                                disabled=True),
                                    make_modal(),
                                ])
                             ]),
                    dbc.Row(id='pandas-output-container-2')
                    ])
                ])),
        ]),
        dcc.Store(id="state-store", data=state_dict)
    ],
    fluid=False,
)

app.layout = layout

@app.callback(
    Output("modal", "is_open"),
    Output("control-input", "value"),
    Input("update-all", "n_clicks"),
    Input("confirm", "n_clicks"),
    Input('cancel', 'n_clicks'),
    State("modal", "is_open"),
    State("control-input", "value")
)
def toggle_modal(update_all_n, confirm_n, cancel_n, is_open, control_input):
    if update_all_n or cancel_n or confirm_n:
        return not is_open, None
    return is_open, None

@app.callback(
    Output("confirm", "disabled"),
    Input("control-input", "value"),
)
def enable_confirm_button(control_input):
    if control_input:
        return False
    return True

@callback(
    Output('datatable-avg', 'data'),
    Output('datatable-avg', 'columns'),
    Input('main-layout', 'children'),
    Input("state-store", "data")
)
def update_output(_, state):

    # get dataframe
    df = pd.DataFrame(state['df'])
    df_avg = get_avg_df(df)

    # round number
    df_avg = round_scenario_columns(df_avg)

    data_df = df_avg.to_dict('records')

    # create column specifications for datatable
    columns=[{'id': c, 'name': c} for c in df_avg.columns if c != 'id']

    return data_df, columns


@callback(
    Output('pandas-output-container-2', 'children'),
    Output("state-store", "data", allow_duplicate=True),
    Output("update-all", "disabled"),
    Input('datatable-avg',  'active_cell'),
    State("state-store", "data"),
    prevent_initial_call=True
)
def render_sub_table(active_cell,state):

    # get dataframes
    df = pd.DataFrame(state['df'])

    if not active_cell:
        raise PreventUpdate

    if active_cell['column_id'] == KEY:
        raise PreventUpdate

    # get subset
    well = state['active_well'] = active_cell['row_id']
    scenario = state['active_scenario'] = active_cell['column_id']
    df_subset = df[df[KEY] == well].drop(columns=[KEY])[['Time', scenario]]

    # get columns
    columns=[{'id': c, 'name': c} for c in df_subset.columns]
    [col_dict.update({'editable':True}) for col_dict in columns if 'Scenario' in col_dict['name']]

    # round table
    df_subset = round_scenario_columns(df_subset)

    child = dash_table.DataTable(
        id='datatable-subset',
        page_size=PAGE_SIZE,
        data = df_subset.to_dict('records'),
        columns=columns
        )
    disable_update_button = False
    return child, state, disable_update_button


@callback(
    Output("state-store", "data", allow_duplicate=True),
    Output('datatable-subset', "data", allow_duplicate=True),

    Input('datatable-subset', 'active_cell'),
    Input("confirm", "n_clicks"),

    State("state-store", "data"),
    State('datatable-subset', "data"),
    State("control-input", "value"),
    prevent_initial_call=True
)
def table_editing(active_cell, confirm_n,
                  state, rows, control_input):

    well = state['active_well']
    scenario = state['active_scenario']
    df = pd.DataFrame(state['df'])

    if "confirm" == ctx.triggered_id and control_input:
        # update with constant values (confirm button in modal)
        new_values = [np.float64(control_input)] * len(df.loc[df[KEY] == well, scenario])
        active_cell = None

    elif not active_cell:
        raise PreventUpdate

    else:
        # update from table input (user changes values manually)
        new_values = pd.DataFrame(rows)[scenario].values
        active_cell = None

    new_rows = pd.DataFrame(rows)
    new_rows[scenario] = new_values
    new_rows = new_rows.to_dict('records')

    df.loc[df[KEY] == well, scenario] = np.float64(new_values)
    state['df'] = df.to_dict()

    return state, new_rows

if __name__ == '__main__':
    app.run(debug=True)
