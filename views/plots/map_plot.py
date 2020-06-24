from datetime import datetime as dt
import plotly.graph_objects as plotgraph
from views.layouts.bar_layouts import map_layout
import numpy as np
import pandas as pd

MAP_STATE = 'state_map_data.csv'
DATA_DIR = 'data'

class MapPlot:

    def get_state_map_data(self):
        state_map = pd.read_csv(f'{DATA_DIR}/{MAP_STATE}')
        print(state_map.columns)
        state_map['Reported'] = pd.to_datetime(state_map['Reported'], format='%Y-%m-%d')
        return state_map

    def __squash(self,x):
        a = x.max()
        return ((np.sqrt(x)/np.sqrt(a))+0.16)*50

    def plot(self):
        states = self.get_state_map_data()
        map = plotgraph.Figure(layout=map_layout)
        hover_txt = states.States.astype(str) + "<br>&#931;: " + states.Sigma.astype(str) + \
                    "<br>Rate of Transmision: "+ states.Rt.astype(str) + \
                    "<br>Population: " + states.Population.apply(lambda x : "{:,}".format(x)).astype(str)

        scatter = plotgraph.Scattergeo(
            locationmode='country names',
            lon=states.Longitude,
            lat=states.Latitude,
            hoverinfo='text',
            text=states.States,
            hovertext=hover_txt,
            mode='markers',
            marker={'colorscale': ['Green', 'Orange', 'Red'], "showscale":True, 'size': self.__squash(states.Sigma), 'color': states.Rt})

        map.update_layout(
            xaxis =  { 'showgrid': False,'zeroline': False,'visible' : False},
            yaxis = {'showgrid': False,'zeroline': False,'visible' : False})

        map.add_trace(scatter)
        day_count = (dt.now() - states["Reported"].min()).days

        return map