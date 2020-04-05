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
from seir.rk4 import Config,epidemic_calculator
from seir.scrap import df
import math

def properties(x):
    grads = list(x.sort_values(by="Date Announced",ascending=True)["Patient Number"].diff(periods=1).fillna(0))
    if len(grads) > 1:
        delta = int(grads[-2])
    else:
        delta = int(grads[-1])
    sigma = int(x["Patient Number"].sum())
    today = int(list(x.sort_values(by="Date Announced",ascending=True)["Patient Number"].fillna(0))[-1])
    frame=list(x.sort_values(by="Date Announced",ascending=True)["Date Announced"].fillna(0))
    first_report =frame[0]
    return pd.Series({"Reported":first_report ,"Sigma":sigma,"Delta":delta,"Today":today, "Day":int((frame[-1]-frame[0]).days) })
    
states = df.groupby(["States","Latitude","Longitude","Date Announced"],as_index=False)["Patient Number"].count()
states = states.groupby(["States","Latitude","Longitude"],as_index=False).apply(properties).reset_index()

def squash(x):
    i =x.min()
    a =x.max()
    return ((x-i)/(a-i))+0.7

current_node = 'India'

fig = go.Figure(layout=dict(height=600,width=580))

hovertxt = states.States.astype(str) + "<br> &#931;: " + states.Sigma.astype(str) + \
"<br> &#916;: " + states.Delta.astype(str)   + "<br> Today: " + states.Today.astype(str) + \
"<br> Day: " + states.Day.astype(str) + "<br> Reported: " + states.Reported.dt.strftime("%d %b")

scatter = go.Scattergeo(
    locationmode='country names',
    lon=states.Longitude,
    lat=states.Latitude,
    hoverinfo='text',
    text=states.States,
    hovertext=hovertxt,
    mode='markers',
    marker={'colorscale':'Inferno','size': squash(states.Sigma)*15, 'color': (1-squash(states.Delta))*50})


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
    html.Div(
        id="time-series-outer",
        className="six columns",
        style={'width': '100%', 'height': '100%',
               'margin': {"r": 0, "t": 0, "l": 0, "b": 0}},
        children=dcc.Loading(
            children=[html.Div(
                id="dropdown-select-outer",
                children=[
                    html.Div(id="selectors",children=[
dcc.Graph(id='map',figure=fig,style={'width': '100%', 'height': '100%', 'margin': { "r": 0, "t": 0, "l": 0, "b": 0}})
                                                ]),
                html.Div(id="plots",children=[
                dcc.Graph(id="seir", figure=epidemic_calculator("India")),
                dcc.Graph(id="seir2", figure=epidemic_calculator("India"))
                        ])
                    ]
        )]
        )
    )

])



@app.callback(
    Output("seir", "figure"),
    [Input("map", "clickData")],
    [State("seir", "figure")],)
def update_time_series(map_click, city):
    if map_click is not None:
        current_node = map_click["points"][0]["text"]
        return epidemic_calculator(current_node)
    else:
        city = city["layout"]["title"]["text"].split(" ")[-1]
        return epidemic_calculator(city)


if __name__ == '__main__':
    app.run_server(debug=True)
