import dash, random
import dash_bootstrap_components as dbc

from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate

table_header = [
    html.Thead(html.Tr([html.Th("Open/Close"), html.Th("First Name"), html.Th("Last Name"), html.Th("Select")]))
]

row1 = html.Tr([
    html.Td(html.I(id={"type":"icon", "index": 1})),
    html.Td("Arthur"),
    html.Td(dbc.Input(value="test 1", type="text", id={"type":"txt-input", "index": 1})),
    html.Td(dbc.Select(id={"type":"select-input", "index": 1}, value="1", options=[{"label": "option 1", "value":"1"}, {"label": "option 2", "value":"2"}])),
    ],
    id={"type":"tr", "index": 1}
)

row1_collapsed = html.Tr(
    html.Td(
        html.Div(id={"type":"hidden", "index": 1}),
        colSpan=4,
    ),
    hidden=True,
    id={"type": "collapsed", "index": 1}
)

row2 = html.Tr([
    html.Td(html.I(id={"type":"icon", "index": 2})),
    html.Td("Ford"),
    html.Td(dbc.Input(value="test 1", type="text", id={"type":"txt-input", "index": 2})),
    html.Td(dbc.Select(id={"type":"select-input", "index": 2}, value="1", options=[{"label": "option 1", "value":"1"}, {"label": "option 2", "value":"2"}])),
    ],
    id={"type":"tr", "index": 2}
)

row2_collapsed = html.Tr(
    html.Td(
        html.Div(id={"type":"hidden", "index": 2}),
        colSpan=4,
    ),
    hidden=True,
    id={"type": "collapsed", "index": 2}
)

row3 = html.Tr([
    html.Td(html.I(id={"type":"icon", "index": 3})),
    html.Td("Zaphod"),
    html.Td(dbc.Input(value="test 1", type="text", id={"type":"txt-input", "index": 3}, disabled=True)),
    html.Td(dbc.Select(id={"type":"select-input", "index": 3}, value="1", disabled=True, options=[{"label": "option 1", "value":"1"}, {"label": "option 2", "value":"2"}])),
    ],
    id={"type":"tr", "index": 3}
)

row3_collapsed = html.Tr(
    html.Td(
        html.Div(id={"type":"hidden", "index": 3}),
        colSpan=4,
    ),
    hidden=True,
    id={"type": "collapsed", "index": 3}
)

row4 = html.Tr([
    html.Td(html.I(id={"type":"icon", "index": 4})),
    html.Td("Trillian"),
    html.Td(dbc.Input(value="test 1", type="text", id={"type":"txt-input", "index": 4}, debounce=True)),
    html.Td(dbc.Select(id={"type":"select-input", "index": 4}, value="1", options=[{"label": "option 1", "value":"1"}, {"label": "option 2", "value":"2"}])),
    ],
    id={"type":"tr", "index": 4}
)

row4_collapsed = html.Tr(
    html.Td(
        html.Div(id={"type":"hidden", "index": 4}),
        colSpan=4,
    ),
    hidden=True,
    id={"type": "collapsed", "index": 4}
)

table_body = [html.Tbody([row1, row1_collapsed, row2, row2_collapsed, row3, row3_collapsed, row4, row4_collapsed])]

table = dbc.Table(table_header + table_body, bordered=True)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])

app.layout = dbc.Container(html.Div([
    table,
    html.Div(id={"type": "div", "index": 1}),
    html.Div(id={"type": "div", "index": 2}),
    html.Div(id={"type": "div", "index": 3}),
    html.Div(id={"type": "div", "index": 4}),
]))


@app.callback(
    Output({"type": "txt-input", "index": MATCH}, 'value'),
    [Input({'type': 'txt-input', 'index': MATCH}, 'value'),
     Input({'type': 'txt-input', 'index': MATCH}, 'id'),
    ]
)
def update_text_input(value, id):
    print("values: " + str(value))
    print("id: " + str(id))
    return str(value)

@app.callback(
    Output({"type": "select-input", "index": MATCH}, 'value'),
    [Input({'type': 'select-input', 'index': MATCH}, 'value'),
     Input({'type': 'select-input', 'index': MATCH}, 'id'),
    ]
)
def update_select_input(value, id):
    print("values: " + str(value))
    print("id: " + str(id))
    return str(value)

@app.callback(
    [Output({"type": "collapsed", "index": MATCH}, 'hidden'),
     Output({"type": "hidden", "index": MATCH}, 'children'),
     Output({"type": "icon", "index": MATCH}, 'className'),
    ],
    [Input({'type': 'icon', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'tr', 'index': MATCH}, 'id'),
     Input({'type': 'collapsed', 'index': MATCH}, 'hidden'),
    ]
)
def update_select_input(n_clicks, id, hidden):
    print("n_clicks: " + str(n_clicks))
    print("hidden:" + str(hidden))
    if n_clicks and n_clicks > 0:
        return not hidden, str(id) + " exposed", "far fa-eye-slash"
    else:
        return hidden, "hidden", "far fa-eye"

app.run_server(debug=True)

if __name__ == '__main__':
    app.run_server(debug=True)
