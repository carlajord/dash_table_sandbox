
import os, sys
import pandas as pd, numpy as np

from dash import Dash, dcc, html
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc

from ui.utils import (FIXED_HEADERS, WELL_NAME_HEADER, VALUE_HEADER,
                      LOWER_BOUND_HEADER, UPPER_BOUND_HEADER, DEFAULT_SCENARIO_COL,
                      get_scenario_cols)
from ui.ui_components import (make_left_panel, make_right_panel,
                              make_main_datatable)

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
UI_PATH = os.path.join(os.path.dirname(__file__), 'ui')


"""
dataiku assets
client = dataiku.api_client()
proj_id = client.get_default_project().project_key
lib_path = f"./project-python-libs/{proj_id}/python/assets"

# create local assets folder
assets_folder = os.path.realpath(os.path.join(sys.argv[1], '../assets'))
os.mkdir(assets_folder)

## Option 1: # this approach works better
# save styles to local assets folder from python library
for asset in os.listdir(lib_path):
    shutil.copy(lib_path + "/" + asset, assets_folder + "/" + asset)
"""


app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP
    ],
    suppress_callback_exceptions=True
)

df_init = pd.read_csv(os.path.join(DATA_PATH,'ForecastScenarios.csv'))

state_dict = {'df': df_init.to_dict(),
              'active_well': None,
              'active_scenario': None,
              'new_scenario_init':[]}

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
    scenario = state['active_scenario']

    state['new_scenario_init'] = df[[LOWER_BOUND_HEADER, UPPER_BOUND_HEADER]].mean(axis=1).values

    children = [
        dbc.Col(id="left-panel", children=make_left_panel(), width=8),
        dbc.Col(id="right-panel", children=[make_right_panel(df, well, scenario)]),
    ]

    return children


## Render main datatable
@callback(
    Output('datatable-main', 'data'),
    Output('datatable-main', 'columns'),
    Output('datatable-main', 'style_data_conditional'),
    Input('load-panels', 'children'),
    Input('trigger-table-update', 'children'),
    State("state-store", "data")
)
def render_main_table(_, trigger, state):

    # get dataframe
    df = pd.DataFrame(state['df'])

    # update the table
    data_df, columns, style = make_main_datatable(df)

    return data_df, columns, style


## Synch state and datatable when removing columns
@callback(
    Output("state-store", "data", allow_duplicate=True),
    Input('datatable-main', 'columns'),
    State("state-store", "data"),
    prevent_initial_call=True
)
def synch_state(columns, state):
    if not columns: raise PreventUpdate

    df = pd.DataFrame(state['df'])
    table_col_names = [d['name'] for d in columns]
    state_col_names = get_scenario_cols(df.head(0))

    cols_to_delete = []
    for s_name in state_col_names:
        if s_name not in table_col_names:
            cols_to_delete.append(s_name)

    if not cols_to_delete: raise PreventUpdate

    # table was deleted, synch state
    df.drop(labels=cols_to_delete, inplace=True, axis=1)
    state['df'] = df.to_dict()

    return state

## Load panel with time step table (the right panel)
@callback(
    Output("right-panel", 'children'),
    Output("state-store", "data", allow_duplicate=True),
    Output("update-all", "disabled"),
    Input('datatable-main',  'active_cell'),
    State("state-store", "data"),
    prevent_initial_call=True
)
def render_sub_table(active_cell,state):

    if not active_cell:
        raise PreventUpdate

    if active_cell['column_id'] in FIXED_HEADERS:
        # only update if the user clicks on scenario column
        raise PreventUpdate

    df = pd.DataFrame(state['df'])
    well = state['active_well'] = active_cell['row_id']
    scenario = state['active_scenario'] = active_cell['column_id']

    child = make_right_panel(df, well, scenario)
    disable_button = False

    return child, state, disable_button


## Change time step table input
@callback(
    Output("state-store", "data", allow_duplicate=True),
    Output('datatable-subset', "data", allow_duplicate=True),
    Output('trigger-table-update', 'children', allow_duplicate=True),

    Input('datatable-subset', 'active_cell'),
    Input("confirm-update-all", "n_clicks"),

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

    if "confirm-update-all" == ctx.triggered_id and control_input:
        # update with constant values (confirm button in update-all modal)
        new_values = [np.float64(control_input)] * len(df.loc[df[WELL_NAME_HEADER] == well, scenario])

    elif not active_cell:
        raise PreventUpdate

    elif None in [well, scenario]:
        raise PreventUpdate

    elif active_cell['column_id'] != VALUE_HEADER:
        raise PreventUpdate

    else:
        # update from table input (user changes values manually)
        new_values = pd.DataFrame(rows)[VALUE_HEADER].values

    new_rows = pd.DataFrame(rows)
    new_rows[VALUE_HEADER] = new_values
    new_rows = new_rows.to_dict('records')

    df.loc[df[WELL_NAME_HEADER] == well, scenario] = np.float64(new_values)
    state['df'] = df.to_dict()

    return state, new_rows, None


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


## Open or close popup to add scenario
@app.callback(
    Output("modal-add-scenario", "is_open"),
    Output("add-scenario-name", "value"),
    Input("add-scenario", "n_clicks"),
    Input("confirm-add-scenario", "n_clicks"),
    Input('cancel-add-scenario', 'n_clicks'),
    State("modal-add-scenario", "is_open")
)
def toggle_modal_add_scenario(add_scenario_n, confirm_n, cancel_n, is_open):
    if add_scenario_n or cancel_n or confirm_n:
        return not is_open, None
    return is_open, None


## Enable / disable button to confirm add scenario
@app.callback(
    Output("confirm-add-scenario", "disabled"),
    Input("add-scenario-name", "value"),
    State("state-store", "data"),
)
def enable_confirm_button_add_scenario(name_input, state):
    df = pd.DataFrame(state['df'])
    col_names = [col.lower() for col in df.columns]
    if name_input and name_input.lower() not in col_names:
        return False
    return True


## Update add scenario and trigger reloading of tables
@app.callback(
    Output('trigger-table-update', 'children', allow_duplicate=True),
    Output("state-store", "data"),
    Input("confirm-add-scenario", "n_clicks"),
    State("state-store", "data"),
    State("add-scenario-name", "value"),
    prevent_initial_call=True
)
def trigger_tables_update(confirm_n, state, scenario):

    if not ("confirm-add-scenario" == ctx.triggered_id and scenario):
        raise PreventUpdate

    df = pd.DataFrame(state['df'])

    # enter the control value for the new scenario
    if DEFAULT_SCENARIO_COL in df.columns:
        new_values = df[DEFAULT_SCENARIO_COL].values
    else:
        new_values = df[[LOWER_BOUND_HEADER, UPPER_BOUND_HEADER]].mean(axis=1).values

    df[scenario] = new_values

    state['df'] = df.to_dict('records')

    return None, state


## Save all scenarios
@app.callback(
    Output("save-scenario-toast", "is_open"),
    Input("save-scenarios", "n_clicks"),
    State("state-store", "data"),
    prevent_initial_call=True
)
def save_table_to_file(_, state):
    return True


if __name__ == '__main__':
    app.run(debug=True)
