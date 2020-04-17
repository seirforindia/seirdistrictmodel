import base64
import json
import dash
from dash.dependencies import State, Input, Output
from io import BytesIO
from core.seir import network_epidemic_calc
from core.scrap import node_config_list, global_dict, get_global_dict, get_nodal_config
import dash_core_components as dcc
import dash_html_components as html
from visuals.vcolumn import map_column, graph_column

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
        return network_epidemic_calc(current_node)
    else:
        city = city["layout"]["title"]["text"].split(" ")[-1]
        return network_epidemic_calc(city)


@app.callback(
    Output("seir2", "figure"),
    [Input("upload-data", "filename"), Input("upload-data", "contents")],
)
def update_output(uploaded_filenames, config_file):
    if config_file is not None:
        config_file = json.loads(base64.b64decode(config_file[28:]).decode('utf-8'))
        if type(config_file) == list:
            get_nodal_config(config_file)
        else :
            get_global_dict(config_file)

    network_epidemic_calc.memo={}
    return network_epidemic_calc("India")

if __name__ == '__main__':
    app.run_server()
