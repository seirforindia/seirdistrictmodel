
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
from seir.rk4 import *

indian_cities = pd.read_csv('data/cities.csv')

fig = go.Figure()

scatter = go.Scattergeo(    
    locationmode = 'country names',
    lon = indian_cities.long,
    lat = indian_cities.lat,
    hoverinfo = 'text',
    text = indian_cities.city,
    hovertext=indian_cities.city,
    mode = 'markers',
    marker = {'size': 2})
    
fig.add_trace(scatter)
fig.update_geos(
    fitbounds="locations", visible=False, resolution=110, scope="asia",
    showcountries=True, countrycolor="Black",
    showsubunits=True, subunitcolor="Blue"
)
fig.update_layout(autosize=False, margin={"r":0,"t":0,"l":0,"b":0},geo={"center": {"lat": 23 ,"lon":77}})



external_stylesheets = ['https://codepen.io/chriddyp/pen/dZVMbK.css']

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Covid-19'),
    
    html.Div(children='''
        Covid-19 Network Analysis
    '''),

    dcc.Graph(
        id='map',
        figure=fig,
        style={'width': '100%', 'display': 'inline-block','height':'100%','vertical-align':'left','margin':{"r":0,"t":0,"l":0,"b":0}}
    ),
    html.Div(
        id="time-series-outer",
        className="six columns",
        style={'width': '50%', 'display': 'inline-block','height':'100%','vertical-align':'top','margin':{"r":0,"t":0,"l":0,"b":0}},
        children=dcc.Loading(
            children=dcc.Graph(
                id="seir",
                figure=epidemic_calculator(dfdt,Config),
            )
        ),
    )

])

@app.callback(
    Output("seir", "figure"),
    [Input("map", "clickData"), Input("map", "figure")])

def update_time_series(choro_click, choro_figure):
    if choro_click is not None:
        for point in choro_click["points"]:
            print(point)

        return epidemic_calculator(dfdt,Config)
    else:
        return epidemic_calculator(dfdt,Config)

if __name__ == '__main__':
    app.run_server(debug=True)