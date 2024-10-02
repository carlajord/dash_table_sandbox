import os

import pandas as pd

from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc

from ui.utils import (make_table_conditional_formatting, PAGE_SIZE,
                      TIME_HEADER, VALUE_HEADER, WELL_NAME_HEADER)

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

def make_subset_datatable(df, well, scenario):

    if None in [well, scenario]:
        df_subset = pd.DataFrame([TIME_HEADER, VALUE_HEADER])
    else:
        df_subset = df[df[WELL_NAME_HEADER] == well][[TIME_HEADER, scenario]]
        df_subset.rename(columns={scenario:VALUE_HEADER}, inplace=True)

    columns = [
        {'id': TIME_HEADER, 'name': TIME_HEADER, 'editable':False},
        {'id': VALUE_HEADER, 'name': VALUE_HEADER, 'editable':True}
    ]
    table = dash_table.DataTable(
        id='datatable-subset',
        page_size=PAGE_SIZE,
        data = df_subset.to_dict('records'),
        columns=columns
        )

    return table

def make_left_panel(df_cols):

    panel = dbc.Card([
    dbc.CardHeader("Scenario Control per Well"),
    dbc.CardBody([
        dbc.Row([html.P("Click on a well scenario to edit controls \
                        for each time step.")]),
        dbc.Row([dash_table.DataTable(
                    id='datatable-main',
                    page_size=PAGE_SIZE,
                    style_data_conditional=make_table_conditional_formatting(df_cols)
                )]),
            ]),
        ])
    return panel

def make_right_panel(df, well=None, scenario=None):

    table = make_subset_datatable(df, well, scenario)

    panel = dbc.Card([
    dbc.CardHeader("Scenario Control per Time Step"),
    dbc.CardBody([
        dbc.Row([html.P(f'Well Name: '), html.B(well)]),
        dbc.Row([dbc.Col(html.P("Enter control value for each time \
                                step or select 'Update All' to enter \
                                constant value."), width=8),
                    dbc.Col([dbc.Button("Update All",
                                        id='update-all',
                                    color="primary",
                                    className="mt-auto"
                                    ),
                        make_modal(),
                    ])
                    ]),
        dbc.Row(table)
        ])
    ])

    return panel
