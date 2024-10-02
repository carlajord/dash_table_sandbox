import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dbc.Row(
            [dbc.Label("Custom header"), dbc.Input(id="input", value="Header")]
        ),
        dbc.Button("toggle", id="open"),
        dbc.Modal(
            [
                dbc.ModalHeader(id="modal-header"),
                dbc.ModalBody("This is the body"),
                dbc.ModalFooter(dbc.Button("close", id="close")),
            ],
            id="modal",
        ),
    ]
)


@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(Output("modal", "children"), [Input("input", "value")])
def set_content(value):
    return [
        dbc.ModalHeader(value),
        dbc.ModalBody(f"Modal with header: {value}"),
        dbc.ModalFooter(dbc.Button("Close", id="close")),
    ]


if __name__ == "__main__":
    app.run_server()
