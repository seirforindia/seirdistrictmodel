from seir.epidemic_calc import network_epidemic_calc
from visuals.map import map, day_count
import dash_core_components as dcc
import dash_html_components as html


map_column = html.Div(id="selectors", children=[
    html.H3("Covid-19 India SEIR Model Day : " + str(day_count)),
    dcc.Graph(id='map', figure=map,
              style={'width': '100%', 'height': '100%', 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}})
])

graph_column = html.Div(id="plots",children=[
    dcc.Graph(id="seir", figure=network_epidemic_calc("India")),
    dcc.Graph(id="seir2", figure=network_epidemic_calc("India"))
])
