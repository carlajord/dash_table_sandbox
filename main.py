
import os, sys
import pandas as pd, numpy as np

from dash import Dash, dcc, html, dash_table
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc

from ui.utils import (round_scenario_columns, get_avg_df,
                      FIXED_HEADERS, WELL_NAME_HEADER, VALUE_HEADER)
from ui.ui_components import (make_left_panel, make_right_panel)

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
UI_PATH = os.path.join(os.path.dirname(__file__), 'ui')

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        FONT_AWESOME
    ],
    suppress_callback_exceptions=True
)

df_init = pd.read_csv(os.path.join(DATA_PATH,'ForecastScenarios.csv'))

state_dict = {'df': df_init.to_dict(),
              'active_well': None,
              'active_scenario': None}

layout = dbc.Container(
    id='main-layout',
    children=[
        dcc.Location(id='url'),
        dbc.Row(html.Br()),
        dbc.Row(
            id="load-panels"),
        dcc.Store(id="state-store", data=state_dict)
    ],
    fluid=False,
)

app.layout = layout

## Load initial page (mostly left panel)
@callback(
    Output('load-panels', 'children'),
    Input('url', 'pathname'),
    State("state-store", "data")
)
def start_page(_, state):

    # initialize with active cell
    df = pd.DataFrame(state['df'])

    well = state['active_well']
    scenario = state['active_scenario']

    df_cols = df.head(0)
    children = [
        dbc.Col(id="left-panel", children=make_left_panel(df_cols), width=8),
        dbc.Col(id="right-panel", children=[make_right_panel(df, well, scenario)]),
    ]

    return children

## Render main datatable
@callback(
    Output('datatable-main', 'data'),
    Output('datatable-main', 'columns'),
    Input('load-panels', 'children'),
    Input('datatable-subset', "data"),
    State("state-store", "data")
)
def render_main_table(_, df_subset, state):

    # get dataframe
    df = pd.DataFrame(state['df'])
    df_avg = get_avg_df(df)

    # round number
    df_avg = round_scenario_columns(df_avg)

    data_df = df_avg.to_dict('records')

    # create column specifications for datatable
    columns=[{'id': c, 'name': c} for c in df_avg.columns if c != 'id']

    return data_df, columns

## Load panel with time step table (the right panel)
@callback(
    Output("right-panel", 'children'),
    Output("state-store", "data", allow_duplicate=True),
    Input('datatable-main',  'active_cell'),
    State("state-store", "data"),
    prevent_initial_call=True
)
def render_sub_table(active_cell,state):

    if not active_cell:
        raise PreventUpdate

    if active_cell['column_id'] in FIXED_HEADERS:
        raise PreventUpdate

    df = pd.DataFrame(state['df'])
    well = state['active_well'] = active_cell['row_id']
    scenario = state['active_scenario'] = active_cell['column_id']

    child = make_right_panel(df, well, scenario)

    return child, state


## Change time step table input
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
        new_values = [np.float64(control_input)] * len(df.loc[df[WELL_NAME_HEADER] == well, scenario])
        active_cell = None

    elif not active_cell:
        raise PreventUpdate

    elif None in [well, scenario]:
        raise PreventUpdate

    elif active_cell['column_id'] != VALUE_HEADER:
        raise PreventUpdate

    else:
        # update from table input (user changes values manually)
        new_values = pd.DataFrame(rows)[VALUE_HEADER].values
        active_cell = None

    new_rows = pd.DataFrame(rows)
    new_rows[VALUE_HEADER] = new_values
    new_rows = new_rows.to_dict('records')

    df.loc[df[WELL_NAME_HEADER] == well, scenario] = np.float64(new_values)
    state['df'] = df.to_dict()

    return state, new_rows

## Open or close popup to change time step table input
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

## Enable / disable button to confirm change in time step table input
@app.callback(
    Output("confirm", "disabled"),
    Input("control-input", "value"),
)
def enable_confirm_button(control_input):
    if control_input:
        return False
    return True

if __name__ == '__main__':
    app.run(debug=True)
