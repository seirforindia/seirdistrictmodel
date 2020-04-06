import dash
from dash.dependencies import State, Input, Output
from seir.rk4 import epidemic_calculator
import dash_core_components as dcc
import dash_html_components as html
from visuals.visual_column import map_column, graph_column

app = dash.Dash(__name__)
server = app.server

app_layout = html.Div(children=[html.Div(id="covidapp", className="two columns", children=dcc.Loading(
    children=[html.Div(id="dropdown-select-outer", children=[map_column, graph_column])]))], style= {"padding":0,"margin":0})
app.layout = app_layout


@app.callback(
    Output("seir", "figure"),
    [Input("map", "clickData")],
    [State("seir", "figure")], )
def update_time_series(map_click, city):
    if map_click is not None:
        current_node = map_click["points"][0]["text"]
        return epidemic_calculator(current_node)
    else:
        city = city["layout"]["title"]["text"].split(" ")[-1]
        return epidemic_calculator(city)


if __name__ == '__main__':
    app.run_server(debug=True)
