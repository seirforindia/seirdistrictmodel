from datetime import datetime as dt
import plotly.graph_objects as go
from visuals.layouts import map_layout
from core.file_locator import get_state_map_data
import plotly.express as px

states = get_state_map_data()

def squash(x):
    i = x.min()
    a = x.max()
    return (((x - i) / (a - i)) + 0.7) * 25


map = go.Figure(layout=map_layout)
hover_txt = states.States.astype(str) + "<br> &#931;: " + states.Sigma.astype(str) + \
            "<br> &#916;: " + states.Delta.astype(str) + "<br> Today: " + states.Today.astype(str) + \
            "<br> Day: " + states.Day.astype(str) + "<br> Reported: " + states.Reported.dt.strftime("%d %b") + \
            "<br> Population: " + states.Population.apply(lambda x : "{:,}".format(x)).astype(str)

scatter = go.Scattergeo(
    locationmode='country names',
    lon=states.Longitude,
    lat=states.Latitude,
    hoverinfo='text',
    text=states.States,
    hovertext=hover_txt,
    mode='markers',
    marker={'colorscale': px.colors.sequential.Peach, "showscale":True, 'size': squash(states.Sigma), 'color': states.Rt})
# px.colors.sequential.Peach, ['Green', 'Yellow', 'Red']
map.update_layout(
    xaxis =  { 'showgrid': False,'zeroline': False,'visible' : False},
    yaxis = {'showgrid': False,'zeroline': False,'visible' : False})

map.add_trace(scatter)
day_count = (dt.now() - states["Reported"].min()).days
