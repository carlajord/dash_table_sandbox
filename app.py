import os, sys
import pandas as pd, numpy as np

import dash
from dash import Dash, dcc, html
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc

from ui.utils_opt import (ID_HEADER, VARIABLE_NAME_HEADER, EDITABLE_COLS, WELL_NAME_HEADER)
from ui.ui_component_opt import (make_left_panel, make_main_datatable, make_right_panel)

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
UI_PATH = os.path.join(os.path.dirname(__file__), 'ui')

ORIGINAL_DATASET = "OptimizationVariablesTable.csv"
MODIFIED_DATASET = "OptimizationVariablesTable.csv"


def get_dataset(dataset_name):
    df = pd.read_csv(os.path.join(DATA_PATH, dataset_name))
    df.reset_index(drop=True, inplace=True)
    if ID_HEADER in df.columns: df.drop(labels=ID_HEADER, axis=1, inplace=True)
    df.insert(0, ID_HEADER, df.index)
    return df

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP
    ],
    suppress_callback_exceptions=True
)

df_init = get_dataset(MODIFIED_DATASET)

state_dict = {'df': df_init.to_dict(),
              'active_well': None
              }

layout = dbc.Container(
    id='main-layout',
    children=[
        dcc.Location(id='url'),
        dbc.Row(html.Br()),
        dbc.Row(
            id="load-panels"),
        dcc.Store(id="state-store", data=state_dict)
    ],
    fluid=True,
)

app.layout = layout

## Load initial page
@callback(
    Output('load-panels', 'children'),
    Input('url', 'pathname'),
    State("state-store", "data")
)
def start_page(_, state):

    df = pd.DataFrame(state['df'])

    well = state['active_well']

    children = [
        dbc.Col(id="left-panel", children=make_left_panel(), width=3),
        dbc.Col(id="right-panel", children=[make_right_panel(df, well)]),
    ]

    return children

## Render main datatable
@callback(
    Output('datatable-main', 'data'),
    Output('datatable-main', 'columns'),
    Input('load-panels', 'children'),
    State("state-store", "data")
)
def render_main_table(_, state):

    # get dataframe
    df = pd.DataFrame(state['df'])

    # update the table
    data_df, columns = make_main_datatable(df)

    return data_df, columns

## Load panel with time step table (the right panel)
@callback(
    Output("right-panel", 'children', allow_duplicate=True),
    Output("state-store", "data", allow_duplicate=True),
    Output("update-all", "disabled"),
    Input('datatable-main',  'active_cell'),
    Input("confirm-reset-table", "n_clicks"),
    State("state-store", "data"),
    prevent_initial_call=True
)
def render_sub_table(active_cell, confirm_n, state):

    if ("confirm-reset-table" == ctx.triggered_id):
        df = get_dataset(ORIGINAL_DATASET)
        child = make_right_panel(df, None)
        disable_button = True
        state['df'] = df.to_dict()

    elif not active_cell:
        raise PreventUpdate

    else:
        df = pd.DataFrame(state['df'])
        well = state['active_well'] = active_cell['row_id']
        child = make_right_panel(df, well)
        disable_button = False

    return child, state, disable_button

## Change time step table input
@callback(
    Output("state-store", "data", allow_duplicate=True),
    Output('datatable-subset', "data", allow_duplicate=True),

    Input('datatable-subset', 'active_cell'),
    Input("confirm-update-all", "n_clicks"),

    State("state-store", "data"),
    State('datatable-subset', "data"),
    State("control-input", "value"),
    State("param-select", "value"),

    prevent_initial_call=True
)
def table_editing(active_cell, confirm_n, state,
                  rows, control_input, param_select):

    # get stored state
    well = state['active_well']
    df = pd.DataFrame(state['df'])

    # get app values
    new_rows = pd.DataFrame(rows)

    # initialize variables
    new_values = None
    col = None
    
    if "confirm-update-all" == ctx.triggered_id and control_input:
        # update with constant values (confirm button in update-all modal)
        new_values = [np.float64(control_input)] * len(df.loc[df[WELL_NAME_HEADER] == well])
        col = param_select
        
    elif not active_cell:
        # no action needed if there is no active cell
        raise PreventUpdate

    elif well is None:
        # no action needed if there is no well or scenario selected
        raise PreventUpdate

    elif active_cell['column_id'] in EDITABLE_COLS:
        # update from table input (user changes values manually)
        if ID_HEADER not in rows[0].keys(): PreventUpdate
        new_values = new_rows[active_cell['column_id']].values
        col = active_cell['column_id']
    
    else:
        raise PreventUpdate

    # place new values in the app table cache
    new_rows[col] = new_values
    
    # update values in the state
    if col == VARIABLE_NAME_HEADER:
        df.loc[df[WELL_NAME_HEADER] == well, VARIABLE_NAME_HEADER] = new_values
    else:
        df.loc[df[WELL_NAME_HEADER] == well, col] = np.float64(new_values)

    new_rows = new_rows.to_dict('records') 
    state['df'] = df.to_dict()

    return state, new_rows


## Open or close popup to change time step table input
@app.callback(
    Output("modal-update-all", "is_open"),
    Output("control-input", "value"),
    Input("update-all", "n_clicks"),
    Input("confirm-update-all", "n_clicks"),
    Input('cancel-update-all', 'n_clicks'),
    State("modal-update-all", "is_open"),
    State("control-input", "value")
)
def toggle_modal_update_all(update_all_n, confirm_n, cancel_n, is_open, control_input):
    if update_all_n or cancel_n or confirm_n:
        return not is_open, None
    return is_open, None


## Enable / disable button to confirm change in time step table input
@app.callback(
    Output("confirm-update-all", "disabled"),
    Input("control-input", "value"),
)
def enable_confirm_button_update_all(control_input):
    if control_input:
        return False
    return True

## Save table
@app.callback(
    Output("save-table-toast", "is_open"),
    Input("save-table", "n_clicks"),
    State("state-store", "data"),
    prevent_initial_call=True
)
def save_table_to_file(_, state):
    #df = pd.DataFrame(state['df'])
    #table_handle = dataiku.Dataset(MODIFIED_DATASET)
    #table_handle.write_with_schema(df) 
    return True

## Open or close popup to confirm reset table
@app.callback(
    Output("modal-reset-table", "is_open"),
    Input("reset-table", "n_clicks"),
    Input("confirm-reset-table", "n_clicks"),
    Input('cancel-reset-table', 'n_clicks'),
    State("modal-reset-table", "is_open"),
    prevent_initial_call=True
)
def toggle_modal_reset_table(reset_n, confirm_n, cancel_n, is_open):
    if reset_n or cancel_n or confirm_n:
        return not is_open
    return is_open

if __name__ == '__main__':
    app.run(debug=True)
