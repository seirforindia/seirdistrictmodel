from datetime import datetime as dt
import plotly.graph_objects as go
from visuals.layouts import map_layout
from core.file_locator import get_state_map_data
import numpy as np

states = get_state_map_data()

def squash(x):
    a = x.max()
    return ((np.sqrt(x)/np.sqrt(a))+0.16)*50


map = go.Figure(layout=map_layout)
hover_txt = states.States.astype(str) + "<br>&#931;: " + states.Sigma.astype(str) + \
            "<br>Rate of Transmision: "+ states.Rt.astype(str) + \
            "<br>Population: " + states.Population.apply(lambda x : "{:,}".format(x)).astype(str)

scatter = go.Scattergeo(
    locationmode='country names',
    lon=states.Longitude,
    lat=states.Latitude,
    hoverinfo='text',
    text=states.States,
    hovertext=hover_txt,
    mode='markers',
    marker={'colorscale': ['Green', 'Orange', 'Red'], "showscale":True, 'size': squash(states.Sigma), 'color': states.Rt})

map.update_layout(
    xaxis =  { 'showgrid': False,'zeroline': False,'visible' : False},
    yaxis = {'showgrid': False,'zeroline': False,'visible' : False})

map.add_trace(scatter)
day_count = (dt.now() - states["Reported"].min()).days
