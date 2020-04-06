from seir.scrap import df, properties, squash
from datetime import datetime as dt
import plotly.graph_objects as go

from visuals.layouts import map_layout

states_series = df.groupby(["States", "Latitude", "Longitude", "Date Announced"], as_index=False)[
    "Patient Number"].count()
states = states_series.groupby(["States", "Latitude", "Longitude"], as_index=False).apply(properties).reset_index()

map = go.Figure(layout=map_layout)

hover_txt = states.States.astype(str) + "<br> &#931;: " + states.Sigma.astype(str) + \
            "<br> &#916;: " + states.Delta.astype(str) + "<br> Today: " + states.Today.astype(str) + \
            "<br> Day: " + states.Day.astype(str) + "<br> Reported: " + states.Reported.dt.strftime("%d %b")

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

day_count = (dt.now() - states_series["Date Announced"].min()).days
