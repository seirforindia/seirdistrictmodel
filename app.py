import base64
import json
import time
import threading
from io import BytesIO
import dash
from dash.dependencies import State, Input, Output
from flask import send_file
import dash_core_components as dcc
import dash_html_components as html

from core.file_locator import download_from_aws, get_district_stats, get_state_stats
download_from_aws()

from visuals.vcolumn import map_column, graph_column, map_dropdown, plot_graph

app = dash.Dash(__name__)
server = app.server

app_layout = html.Div(
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
app.layout = app_layout


district_stats_data = get_district_stats()
print(f'district data till date {district_stats_data[0]["Date Announced"][-1]}')
state_stats_data = get_state_stats()
print(f'state data till date {state_stats_data[0]["Date Announced"][-1]}')

@app.callback(
    [Output("seir", "figure"), Output('seir2', 'figure')],
    [Input("districtList", "value")])
def update_time_series(selected_district):
    # print(locals())
    if selected_district:
        district_data = list(filter(lambda node: (node["District"]+','+node['State']
                        ) == selected_district, district_stats_data))
        if not district_data :
            raise Exception(f"District data not found for selected state: {selected_district}")
        district_data = district_data[0]
        dist_name = selected_district.split(',')[0] if selected_district.split(',')[0]\
             != 'unknown' else selected_district.replace(',','-')
        district_graph = plot_graph(district_data["I"], district_data["R"], district_data["hospitalized"],
                                    district_data["fatal"], district_data["Rt"], district_data["Date Announced"],
                                    district_data["cumsum"], district_data["Mt"], dist_name)
        state_data = list(filter(lambda node: node["State"] == district_data['State'], state_stats_data))
        if not state_data:
            raise Exception(f"Data not found for selected state: {district_data['State']}")

        state_data = state_data[0]
        state_graph = plot_graph(state_data["I"], state_data["R"], state_data["hospitalized"],
                             state_data["fatal"], state_data["Rt"], state_data["Date Announced"],
                             state_data["cumsum"], state_data["Mt"], district_data['State'],
                             state_data['test_per'])
        return district_graph, state_graph

    node_india = list(filter(lambda node: node["State"] == 'India', state_stats_data))[0]
    india_graph = plot_graph(node_india["I"], node_india["R"], node_india["hospitalized"],
                            node_india["fatal"], node_india["Rt"], node_india["Date Announced"],
                            node_india["cumsum"], node_india["Mt"], node_india['State'],
                            node_india['test_per'])
        
    return india_graph, india_graph

@app.callback(
    [Output("districtList", "options"), Output("districtList", "value")],
    [Input("map", "clickData"),Input("sort-by", "value")])
def update_dropdown_list(map_click, sort_by):
    # print(locals())
    if map_click:
        selected_state = map_click['points'][0]['text']
        options = []
        dist_for_a_state = list(filter(
            lambda node: node["State"] == selected_state, district_stats_data))
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
        dist_for_a_state = [i for i in district_stats_data if i['cumsum'][-1]>300]
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

if __name__ == '__main__':  
    app.run_server(debug=True)
