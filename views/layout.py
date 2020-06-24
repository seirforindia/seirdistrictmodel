import dash_core_components as dcc
import dash_html_components as html
from visuals.vcolumn import map_column, graph_column
import json

DATA_DIR = 'data'
STATE_STATS = 'state_stats.json'
DISTRICT_STATS = 'district_stats.json'

class Layout:

    def get_district_stats(self):
        with open(f"{DATA_DIR}/{DISTRICT_STATS}") as district_robj:
            return json.loads(district_robj.read())

    def get_state_stats(self):
        with open(f"{DATA_DIR}/{STATE_STATS}") as state_robj:
            return json.loads(state_robj.read())

    @staticmethod
    def base_layout():
        return html.Div(
            children=[
                html.Div(id="covidapp", className="two columns",
                         children=dcc.Loading(
                             children=[html.Div(id="dropdown-select-outer",
                                                children=[map_column, graph_column]
                                                )]
                         )
                         )
            ], style= {"padding":0,"margin":0}
        )
