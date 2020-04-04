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

label = indian_cities.loc[:,["city","city"]]
label.columns=["label","value"]

current_node='India'
fig = go.Figure()

scatter = go.Scattergeo(    
    locationmode = 'country names',
    lon = indian_cities.long,
    lat = indian_cities.lat,
    hoverinfo = 'text',
    text = indian_cities.city,
    hovertext=indian_cities.city,
    mode = 'markers',
    marker = {'size': 2,'color':"green"},selectedpoints = {"marker" : {'size': 2,"color": "red"}})

    
fig.add_trace(scatter)
fig.update_geos(
    fitbounds="locations", visible=False, resolution=110, scope="asia",
    showcountries=True, countrycolor="Black",
    showsubunits=True, subunitcolor="Blue"
)
fig.update_layout(autosize=False, margin={"r":0,"t":0,"l":0,"b":0},geo={"center": {"lat": 23 ,"lon":77}})



external_stylesheets = ['https://codepen.io/chriddyp/pen/dZVMbK.css']

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(children=[
    html.H1(children='Covid-19'),
    
    html.Div(children='''
        Covid-19 Network Analysis
    '''),

    dcc.Graph(
        id='map',
        figure=fig,
        style={'width': '100%', 'display': 'inline-block','height':'100%','margin':{"r":0,"t":0,"l":0,"b":0}}
    ),
    html.Div(
        id="time-series-outer",
        className="six columns",
        style={'width': '100%', 'display': 'inline-block','height':'100%','margin':{"r":0,"t":0,"l":0,"b":0}},
        children=dcc.Loading(
            children=[html.Div(
                    id="dropdown-select-outer",
                    children=[html.Div(
                            [
                                html.P("Transformation Selector"),
                                dcc.Dropdown(
                                    id="dropdown-select",
                                    options=[
                                        {"label": "Log-Transform", "value": "log"},
                                        {"label": "Linear", "value": "linear"},
                                    ],
                                    value="linear",
                                ),
                            ],className="selector"),
                                html.Div(
                                    [
                                        html.P("Current"),
                                        html.Div("India",id="city-select"),
                                    ],
                            className="city"),
                            html.Div(
                                    [
                                        html.P("Reset"),
                                        html.Button("Reset",id="reset"),
                                    ],
                            className="Reset",style={"padding-left":34})]),
                dcc.Graph(id="seir",figure=epidemic_calculator(dfdt,Config,"India","linear"))
                
                ]
        )
    )       

])

@app.callback(
    [Output("seir", "figure"),Output("city-select", "children")],
    [Input("map", "clickData"), Input("dropdown-select", "value")], 
    [State("dropdown-select", "value"),State("city-select", "children")],)
    
def update_time_series(map_click,select,log_linear,city):
    if map_click is not None:
        current_node = map_click["points"][0]["text"]
        return epidemic_calculator(dfdt,Config,current_node,log_linear),str(current_node)
    else:
        return epidemic_calculator(dfdt,Config,city,log_linear),city


@app.callback(
    [Output("map", "clickData")],
    [Input("reset", "n_clicks")], 
    [State("dropdown-select", "value")],)
    
def reset(n_clicks,log_linear):
    return [{'points': [{'curveNumber': 0, 'pointNumber': 574, 'pointIndex': 574, 'lon': 75.78, 'lat': 23.19, 'location': None, 'text': ' India', 'hovertext': ' India'}]}]


if __name__ == '__main__':
    app.run_server(debug=True)