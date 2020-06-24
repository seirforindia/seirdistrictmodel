from dash.dependencies import Input, Output
from visuals.vcolumn import plot_graph
import json

DATA_DIR = 'data'
DISTRICT_STATS = 'district_stats.json'
STATE_STATS = 'state_stats.json'

class TimeSeriesView:

    def __init__(self, app):
        self.app = app

    def layout(self):
        return

    def output(self):
        return [Output("seir", "figure"), Output('seir2', 'figure')]

    def input(self):
        return [Input("districtList", "value")]

    def update(self, selected_district):

        if selected_district:
            district_data = list(filter(lambda node: (node["District"]+','+node['State']
                                                      ) == selected_district, self.get_district_stats()))
            if not district_data :
                raise Exception(f"District data not found for selected state: {selected_district}")
            district_data = district_data[0]
            dist_name = selected_district.split(',')[0] if selected_district.split(',')[0] \
                                                           != 'unknown' else selected_district.replace(',','-')
            district_graph = plot_graph(district_data["I"], district_data["R"], district_data["hospitalized"],
                                        district_data["fatal"], district_data["Rt"], district_data["Date Announced"],
                                        district_data["cumsum"], district_data["Mt"], dist_name)
            state_data = list(filter(lambda node: node["State"] == district_data['State'], self.get_state_stats()))
            if not state_data:
                raise Exception(f"Data not found for selected state: {district_data['State']}")

            state_data = state_data[0]
            state_graph = plot_graph(state_data["I"], state_data["R"], state_data["hospitalized"],
                                     state_data["fatal"], state_data["Rt"], state_data["Date Announced"],
                                     state_data["cumsum"], state_data["Mt"], district_data['State'],
                                     state_data['test_per'])
            return district_graph, state_graph

        node_india = list(filter(lambda node: node["State"] == 'India', self.get_state_stats()))[0]
        india_graph = plot_graph(node_india["I"], node_india["R"], node_india["hospitalized"],
                                 node_india["fatal"], node_india["Rt"], node_india["Date Announced"],
                                 node_india["cumsum"], node_india["Mt"], node_india['State'],
                                 node_india['test_per'])

        return india_graph, india_graph


    def get_district_stats(self):
        with open(f"{DATA_DIR}/{DISTRICT_STATS}") as district_robj:
            return json.loads(district_robj.read())

    def get_state_stats(self):
        with open(f"{DATA_DIR}/{STATE_STATS}") as state_robj:
            return json.loads(state_robj.read())

    def register_to_dash_app(self):
        @self.app.callback(self.output(), self.input())
        def func(selected_district):
            return self.update(selected_district)
