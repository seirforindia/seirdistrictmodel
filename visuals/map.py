from core.scrap import states, squash
from datetime import datetime as dt
import plotly.graph_objects as go
from visuals.layouts import map_layout


map = go.Figure(layout=map_layout)
hover_txt = states.States.astype(str) + "<br> &#931;: " + states.Sigma.astype(str) + \
            "<br> &#916;: " + states.Delta.astype(str) + "<br> Today: " + states.Today.astype(str) + \
            "<br> Day: " + states.Day.astype(str) + "<br> Reported: " + states.Reported.dt.strftime("%d %b") + \
            "<br> Population: " + states.Population.astype(str)

scatter = go.Scattergeo(
    locationmode='country names',
    lon=states.Longitude,
    lat=states.Latitude,
    hoverinfo='text',
    text=states.States,
    hovertext=hover_txt,
    mode='markers',
    marker={'colorscale': 'Reds',"showscale":True, 'size': squash(states.Sigma) * 25, 'color': states.Delta})

map.add_trace(scatter)
day_count = (dt.now() - states["Reported"].min()).days
