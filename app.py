import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dash.dependencies import State, Input, Output
from dash.exceptions import PreventUpdate
import pymapd
import datetime
from datetime import datetime as dt
import os
import time
import json
from seir.rk4 import *

indian_cities = pd.read_csv('data/cities.csv')

label = indian_cities.loc[:, ["city", "city"]]
label.columns = ["label", "value"]

current_node = 'India'

fig = go.Figure(layout=dict(height=600,width=580))

scatter = go.Scattergeo(
    locationmode='country names',
    lon=indian_cities.long,
    lat=indian_cities.lat,
    hoverinfo='text',
    text=indian_cities.city,
    hovertext=indian_cities.city,
    mode='markers',
    marker={'size': 2, 'color': "green"})


fig.add_trace(scatter)

fig.update_layout(title="Covid-19 Intervention Modelling",  autosize=False,
                  margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  geo = go.layout.Geo(
                        center= {"lat": 23, "lon": 82.5},
                        resolution = 110,
                        scope = 'asia',
                        showframe = True,
                        showcoastlines = True,
                        fitbounds="locations",
                        landcolor = "rgb(229, 229, 229)",
                        countrycolor = "white" ,
                        coastlinecolor = "white",
                        projection_type = 'mercator',
                        lonaxis_range= [ -4.0, 26.0 ],
                        lataxis_range= [ -10.5, 20.0 ],
                        domain = dict(x = [ 0, 1 ], y = [ 0, 1 ]))
                        )


external_stylesheets = ['https://codepen.io/chriddyp/pen/dZVMbK.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(children=[
    html.H1(children='Covid-19'),

    html.Div(children='''
        Covid-19 Intervention Modelling
    '''),

    dcc.Graph(
        id='map',
        figure=fig,
        style={'width': '100%', 'height': '100%', 'margin': {
            "r": 0, "t": 0, "l": 0, "b": 0}, "padding-left": 34}
    ),
    html.Div(
        id="time-series-outer",
        className="six columns",
        style={'width': '100%', 'height': '100%',
               'margin': {"r": 0, "t": 0, "l": 0, "b": 0}},
        children=dcc.Loading(
            children=[html.Div(
                id="dropdown-select-outer",
                children=[html.Div([
                    html.P("Transformation Selector"),
                    dcc.Dropdown(
                        id="dropdown-select",
                        options=[
                            {"label": "Log-Transform", "value": "log"},
                            {"label": "Linear", "value": "linear"},
                        ],
                        value="linear",
                    ), ], className="selector"), dcc.Graph(id="seir", figure=epidemic_calculator(dfdt, Config, "India", "linear")),
                    dcc.Graph(id="seir2", figure=epidemic_calculator(dfdt, Config, "India", "linear"))]
            )
            ]
        )
    )

])


@app.callback(
    Output("seir", "figure"),
    [Input("map", "clickData")],
    [State("dropdown-select", "value"), State("seir", "figure")],)
def update_time_series(map_click, log_linear, city):
    if map_click is not None:
        current_node = map_click["points"][0]["text"]
        return epidemic_calculator(dfdt, Config, current_node, log_linear)
    else:
        city = city["layout"]["title"]["text"].split(" ")[-1]
        return epidemic_calculator(dfdt, Config, city, log_linear)


if __name__ == '__main__':
    app.run_server(debug=True)
