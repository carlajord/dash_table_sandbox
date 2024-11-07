import os

import pandas as pd

from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc

from ui.utils_opt import (PAGE_SIZE, ID_HEADER, VARIABLE_NAME_HEADER, INIT_VALUE_HEADER, WELL_NAME_HEADER,
                      WELL_TYPE_HEADER, LOWER_BOUND_HEADER, UPPER_BOUND_HEADER, SUBSET_COLS,
                      EDITABLE_COLS)

def make_modal_update_all():

    """
    Pop-up to overwrite optimization parameters by a constant number.
    """
    parameter_select_options = [{'label': val, "value": val} for val in EDITABLE_COLS if val != VARIABLE_NAME_HEADER]

    modal = dbc.Modal([
                dbc.ModalBody([
                    dbc.Row(html.P("Select an optimization parameter:")),
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("Value:"),
                            dbc.Select(
                                id="param-select",
                                options=parameter_select_options
                            )
                        ]
                    ),
                    dbc.Row(html.P("Enter value to overwrite optimization parameter for all time steps.")),
                    dbc.Row(dbc.InputGroup(children=[dbc.InputGroupText("Value:"),
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

    df_main = df[[WELL_NAME_HEADER, WELL_TYPE_HEADER]].groupby(by=[WELL_NAME_HEADER]).first().reset_index()
    df_main.insert(0, ID_HEADER, df_main[WELL_NAME_HEADER].values)
    data_df = df_main.to_dict('records')

    # create column specifications for datatable
    columns=[{'id': c, 'name': c} for c in df_main.columns if c != ID_HEADER]

    return data_df, columns

def make_subset_datatable(df, well):
    
    if well is None:
        df_subset = pd.DataFrame(SUBSET_COLS)
    else:
        
        df_subset = df[df[WELL_NAME_HEADER] == well][SUBSET_COLS]
    
    # create column specifications for datatable
    columns=[{'id': c, 'name': c} for c in SUBSET_COLS if c != ID_HEADER]

    [col_def.update({'editable': False}) for col_def in columns if col_def['name'] not in EDITABLE_COLS]

    style_data_conditional = [{
        'if': {
            'filter_query': f'{{{INIT_VALUE_HEADER}}} > {{{UPPER_BOUND_HEADER}}}',
            'column_id': INIT_VALUE_HEADER
        },
        'color': 'red',
        'fontWeight': 'bold'
        },
        {
        'if': {
            'filter_query': f'{{{INIT_VALUE_HEADER}}} < {{{LOWER_BOUND_HEADER}}}',
            'column_id': INIT_VALUE_HEADER
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
        columns=columns,
        style_data_conditional=style_data_conditional,
        style_cell={'textAlign': 'center'}
        )

    return table

def make_left_panel():

    """
    Panel that includes the main table with well names.
    """

    panel = dbc.Card([
    dbc.CardHeader("Wells"),
    dbc.CardBody([
        dbc.Row([
            dbc.Col(html.P("Click on a well to edit optimization parameters."))
        ]),
        dbc.Row(html.Br()),
        dbc.Row([
            dash_table.DataTable(
                    id='datatable-main',
                    page_size=PAGE_SIZE,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'minWidth': '70px', 'width': '70px', 'maxWidth': '70px',
                        'textAlign': 'center'
                    }
                )]),
        dbc.Row(html.Br())
        ]),
    ])
    return panel

def make_right_panel(df, well=None):

    """
    Panel that includes the subset table with optimization parameters.
    """

    # dummy for initialization of the app
    well_name = [html.Div()]

    # after initialized we will have well defined
    if well is not None:
        well_name = [dbc.Row([
                dcc.Markdown([f'Well Name:  **{well}**'],
                            style={'overflow': 'hidden'}),
                dcc.Markdown(id="bound-frame",
                            style={'overflow': 'hidden'})
            ]),
            dbc.Row(html.Hr())]

    table = make_subset_datatable(df, well)

    header_and_table = [
        dbc.Row([dbc.Col(html.P("Change optimization parameters for each time \
                                step or select 'Update All' to enter \
                                constant value for a given parameter.")),
                        dbc.Col(html.Div(
                                children = [
                                    dbc.Button("Update All", id='update-all', disabled=True, size="sm"),
                                    dbc.Button("Save Table", id='save-table',size="sm"),
                                    dbc.Button("Reset Table", id='reset-table',size="sm")
                                ],
                                className="d-grid gap-2 d-md-flex justify-content-md-end")
                            ),
                        make_modal_update_all(),
                        make_modal_reset_table(),
                        dbc.Toast(
                            [html.P("Table has been saved!", className="mb-0")],
                                id="save-table-toast",
                                header="Success",
                                duration=2000,
                                is_open=False,
                                style={"position": "fixed", "top": 10, "right": 10, 'width':250},
                            ),
                    ]),
        dbc.Row(table),
        html.Div(id='trigger-subset-table-update')
    ]
    panel = dbc.Card([
    dbc.CardHeader("Optimization Parameters"),
    dbc.CardBody(well_name+header_and_table)
    ])

    return panel