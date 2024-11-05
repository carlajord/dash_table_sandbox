import os

import pandas as pd

from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc

from ui.utils import (PAGE_SIZE, ID_HEADER, TIME_HEADER, VALUE_HEADER, WELL_NAME_HEADER,
                      LOWER_BOUND_HEADER, UPPER_BOUND_HEADER, WELL_CONTROL_HEADER,
                      VARIABLE_NAME_HEADER, VARIABLE_NAME_ORIGINAL)

from ui.utils import  (make_table_conditional_formatting, get_avg_df,
                       get_scenario_cols)

def make_modal_update_all():

    """
    Pop-up to overwrite control values by a constant number.
    """

    modal = dbc.Modal([
                dbc.ModalBody([
                    dbc.Row(html.P("Enter value to overwrite control for all time steps.")),
                    dbc.Row(dbc.InputGroup(children=[dbc.InputGroupText("Control Value:"),
                                                        dbc.Input(id="control-input",
                                                                  type="number")],
                                            className="mb-3")),
                    ]),
                dbc.ModalFooter([
                    dbc.Row(children=[
                    dbc.Col(dbc.Button("Confirm", id="confirm-update-all",
                                       size="sm", n_clicks=0)),
                    dbc.Col(dbc.Button("Cancel", id="cancel-update-all",
                                       size="sm", n_clicks=0))
                    ], justify='end')
                    ]
                ),
            ],
    id="modal-update-all",
    is_open=False,
    )
    return modal

def make_modal_add_scenario():

    """
    Pop-up to add a new scenario column.
    """

    modal = dbc.Modal([
                dbc.ModalBody([
                    dbc.Row(html.P("Enter scenario name and control value for all time steps.")),
                    dbc.Row(dbc.InputGroup(children=[dbc.InputGroupText("Scenario Name:"),
                                                        dbc.Input(id="add-scenario-name",
                                                                  type="text")],
                                            className="mb-3"))
                    ]),
                dbc.ModalFooter([
                    dbc.Row(children=[
                        dbc.Col(dbc.Button("Confirm", id="confirm-add-scenario",
                                       n_clicks=0, disabled=True, size="sm")),
                        dbc.Col(dbc.Button("Cancel", id="cancel-add-scenario",
                                        size="sm", n_clicks=0))
                    ], justify='end')
                    ]
                ),
            ],
    id="modal-add-scenario",
    is_open=False,
    )
    return modal

def make_modal_reset_table():

    """
    Pop-up to confirm reset table to original.
    """

    modal = dbc.Modal([
                dbc.ModalBody([
                    dbc.Row(html.P("All variables and values will be reset to the original table.")),
                    ]),
                dbc.ModalFooter([
                    dbc.Row(children=[
                        dbc.Col(dbc.Button("Confirm", id="confirm-reset-table",
                                       n_clicks=0, size="sm")),
                        dbc.Col(dbc.Button("Cancel", id="cancel-reset-table",
                                        size="sm", n_clicks=0))
                    ], justify='end')
                    ]
                ),
            ],
    id="modal-reset-table",
    is_open=False,
    )
    return modal

def make_main_datatable(df):

    scenario_cols = get_scenario_cols(df.head(0))

    df_avg = get_avg_df(df)

    data_df = df_avg.to_dict('records')

    # create column specifications for datatable
    columns=[{'id': c, 'name': c} for c in df_avg.columns if c != 'id']

    [col_def.update({'deletable': True}) for col_def in columns if col_def['name'] in scenario_cols]

    style = make_table_conditional_formatting(df_avg.head(0))
    return data_df, columns, style

def make_subset_datatable(df, well, scenario):

    """
    Makes time step datatable, includes formatting for out of bound values.
    """

    if None in [well, scenario]:
        df_subset = pd.DataFrame([ID_HEADER, VARIABLE_NAME_ORIGINAL, TIME_HEADER, WELL_CONTROL_HEADER, VALUE_HEADER])
    else:
        
        df_subset = df[df[WELL_NAME_HEADER] == well][[ID_HEADER, TIME_HEADER, WELL_CONTROL_HEADER, scenario,
                                                      LOWER_BOUND_HEADER, UPPER_BOUND_HEADER]]
        df_subset.rename(columns={scenario:VALUE_HEADER}, inplace=True)

        variable_name_col = VARIABLE_NAME_ORIGINAL
        for col in df.columns:
            if col.startswith(VARIABLE_NAME_HEADER) and scenario in col:
                variable_name_col = col
                break
        # fix dollar sign for markdown
        df_subset.insert(1, VARIABLE_NAME_HEADER, df[variable_name_col])#.map(lambda x: x.replace("$", "\$")))
        
    column = [
        {'id': VARIABLE_NAME_HEADER, 'name': VARIABLE_NAME_HEADER, 'editable':True},
        {'id': TIME_HEADER, 'name': TIME_HEADER, 'editable':False},
        {'id': WELL_CONTROL_HEADER, 'name': WELL_CONTROL_HEADER, 'editable':False},
        {'id': VALUE_HEADER, 'name': VALUE_HEADER, 'editable':True}
    ]

    style_data_conditional = [{
        'if': {
            'filter_query': f'{{{VALUE_HEADER}}} > {{{UPPER_BOUND_HEADER}}}',
            'column_id': VALUE_HEADER
        },
        'color': 'red',
        'fontWeight': 'bold'
        },
        {
        'if': {
            'filter_query': f'{{{VALUE_HEADER}}} < {{{LOWER_BOUND_HEADER}}}',
            'column_id': VALUE_HEADER
        },
        'color': 'red',
        'fontWeight': 'bold'
        }
    ]

    table = dash_table.DataTable(
        id='datatable-subset',
        page_size=PAGE_SIZE,
        editable=True,
        data = df_subset.to_dict('records'),
        columns=column,
        style_data_conditional=style_data_conditional,
        style_cell={'textAlign': 'center'}
        )

    return table

def make_left_panel():

    """
    Panel that includes the main table with well names.
    """

    panel = dbc.Card([
    dbc.CardHeader("Scenario Control per Well"),
    dbc.CardBody([
        dbc.Row([
            dbc.Col(html.P("Click on a well scenario to edit controls \
                        for each time step."), width=8),
            dbc.Col(html.Div(
                children = [
                    dbc.Button("Add Scenario", id='add-scenario',size="sm"),
                    dbc.Button("Save Scenarios", id='save-scenarios', size="sm"),
                    dbc.Button("Reset Table", id='reset-table',size="sm")
                ],
                className="d-grid gap-2 d-md-flex justify-content-md-end")
                ),
            dbc.Toast(
                [html.P("Senarios have been saved!", className="mb-0")],
                    id="save-scenario-toast",
                    header="Success",
                    duration=2000,
                    is_open=False,
                    style={"position": "fixed", "top": 10, "right": 10, 'width':250},
                ),
        ]),
        dbc.Row(html.Br()),
        dbc.Row([
            html.Div(id='trigger-table-update'),
            dash_table.DataTable(
                    id='datatable-main',
                    page_size=PAGE_SIZE,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'minWidth': '80px', 'width': '80px', 'maxWidth': '80px',
                        'textAlign': 'center'
                    }
                )]),
        dbc.Row(html.Br()),
        make_modal_add_scenario(),
        make_modal_reset_table(),
        ]),
    ])
    return panel

def make_right_panel(df, well=None, scenario=None):

    """
    Panel that includes the subset table with time steps.
    """

    # dummy for initialization of the app
    well_scenario_name = [html.Div()]

    # after initialized we will have well and scenario defined
    if None not in [well, scenario]:
        well_scenario_name = [dbc.Row([
                dcc.Markdown([f'Well Name:  **{well}**  \nScenario:  **{scenario}**'],
                            style={'overflow': 'hidden'}),
                dcc.Markdown(id="bound-frame",
                            style={'overflow': 'hidden'})
            ]),
            dbc.Row(html.Hr())]

    table = make_subset_datatable(df, well, scenario)

    header_and_table = [
        dbc.Row([dbc.Col(html.P("Enter control value for each time \
                                step or select 'Update All' to enter \
                                constant value."), width=8),
                    dbc.Col([dbc.Button("Update All",
                                        id='update-all',
                                    disabled=True,
                                    size="sm"
                                    ),
                        make_modal_update_all(),
                    ])
                    ]),
        dbc.Row(table),
        html.Div(id='trigger-subset-table-update')
    ]
    panel = dbc.Card([
    dbc.CardHeader("Scenario Control per Time Step"),
    dbc.CardBody(well_scenario_name+header_and_table)
    ])

    return panel

def make_bound_frame(lower, upper):

    content = [f'Lower Bound:  **{lower}**  \nUpper Bound:  **{upper}**']

    return content