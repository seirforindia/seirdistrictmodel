from dash.dependencies import Input, Output
import json

class DropDownView:

    def __init__(self, app, RESOURCE_CONFIG):
        self.app = app
        self.RESOURCE_CONFIG = RESOURCE_CONFIG

    def layout(self):
        return

    def output(self):
        return [Output("districtList", "options"), Output("districtList", "value")]

    def input(self):
        return  [Input("map", "clickData"),Input("sort-by", "value")]

    def update(self, map_click, sort_by):

        if map_click:
            selected_state = map_click['points'][0]['text']
            options = []
            dist_for_a_state = list(filter(
                lambda node: node["State"] == selected_state, self.get_district_stats()))
            if not dist_for_a_state:
                raise Exception(f"Data not found for selected state: {map_click}")
            if sort_by == "hospitalized":
                dist_for_a_state.sort(key=lambda x: (x[sort_by][-5]- x[sort_by][-35]), reverse=True)
                options = []
                for node in dist_for_a_state:
                    new_host = node[sort_by][-5] - node[sort_by][-35]
                    if node['District'] == 'unknown':
                        label = f"{node['State'].upper()} - {node['District'].upper()} ({new_host:.0f})"
                    else:
                        label = f"{node['District'].upper()} ({new_host:.0f})"
                    options.append({'label':label, 'value':node["District"]+','+node['State']})
            else:
                dist_for_a_state.sort(key=lambda x: (x[sort_by], (x["hospitalized"][-5]- x["hospitalized"][-35])), reverse=True)
                options = []
                for node in dist_for_a_state:
                    if node['District'] == 'unknown':
                        label = f"{node['State']} - {node['District'].upper()} ({node[sort_by]})"
                    else:
                        label = f"{node['District'].upper()} ({node[sort_by]})"
                    options.append({'label':label, 'value':node["District"]+','+node['State']})

            return options, options[0]['value']
        else:
            dist_for_a_state = [i for i in self.get_district_stats() if i['cumsum'][-1]>300]
            if sort_by == "hospitalized":
                options=[]
                dist_for_a_state.sort(key=lambda x: (x[sort_by][-5]- x[sort_by][-35]), reverse=True)
                for node in dist_for_a_state:
                    new_host = node[sort_by][-5] - node[sort_by][-35]
                    if node['District'] == 'unknown':
                        label = f"{node['State']} - {node['District'].upper()} ({new_host:.0f})"
                    else:
                        label = f"{node['District'].upper()} ({new_host:.0f})"
                    options.append({'label':label, 'value':node["District"]+','+node['State']})
            else:
                dist_for_a_state.sort(key=lambda x: (x[sort_by], (x["hospitalized"][-5]- x["hospitalized"][-35])), reverse=True)
                options = []
                for node in dist_for_a_state:
                    if node['District'] == 'unknown':
                        label = f"{node['State']} - {node['District'].upper()} ({node[sort_by]})"
                    else:
                        label = f"{node['District'].upper()} ({node[sort_by]})"
                    options.append({'label':label, 'value':node["District"]+','+node['State']})
            return options, None

    def get_district_stats(self):
        DATA_DIR = self.RESOURCE_CONFIG.get('PATH','DATA_DIR')
        DISTRICT_STATS = self.RESOURCE_CONFIG.get('STATS','DISTRICT_STATS')
        with open(f"{DATA_DIR}/{DISTRICT_STATS}") as district_robj:
            return json.loads(district_robj.read())

    def register_to_dash_app(self):
        @self.app.callback(self.output(), self.input())
        def func(map_click, sort_by):
            return self.update(map_click, sort_by)
