import base64
import json
import threading
from io import BytesIO
import dash
from dash.dependencies import State, Input, Output
from flask import send_file
from core.file_locator import download_from_aws, get_district_stats, get_state_stats
import dash_core_components as dcc
import dash_html_components as html
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


@app.callback(
    [Output("seir", "figure"), Output('seir2', 'figure'), Output("districtList", "options")],
    [Input("map", "clickData"), Input("districtList", "value"), Input("sort-by", "value")],
    [State("seir", "figure")], )
def update_time_series(map_click, selected_district, sort_by, city):
    options = []
    current_node = map_click["points"][0]["text"] if map_click else "India"

    state_data = list(filter(lambda node: node["State"] == current_node, state_stats_data))
    if not state_data:
        raise Exception(f"Data not found for selected state: {current_node}")

    state_data = state_data[0]
    state_graph = plot_graph(state_data["I"], state_data["R"], state_data["hospitalized"],
                             state_data["fatal"], state_data["Rt"], state_data["Date Announced"],
                             state_data["cumsum"], current_node)

    if not map_click:
        return state_graph, state_graph, []

    district_list_of_selected_state = list(filter(
        lambda node: node["State"] == current_node, district_stats_data))

    if sort_by == "cumsum":
        district_list_of_selected_state.sort(key=lambda x: x[sort_by][-1], reverse=True)
        options = [{"label": f"{node['District'].upper()} ({node[sort_by][-1]})\
                  ({node['Rt']})", "value": node["District"]+','+node['State']}\
                  for node in district_list_of_selected_state]
    else:
        district_list_of_selected_state.sort(key=lambda x: (x[sort_by], x["cumsum"][-1]), reverse=True)
        options = [{"label": f"{node['District'].upper()} ({node[sort_by]})",
                  "value": node["District"]+','+node['State']}\
                   for node in district_list_of_selected_state]

    if not district_list_of_selected_state :
        raise Exception(f"District data not found for select state: {current_node}")

    if selected_district:
        options_value_list = [option["value"] for option in options]
        selected_district = selected_district if selected_district in \
                            options_value_list else options_value_list[0]
    else:
        selected_district = options[0]["value"]

    district_data = list(filter(lambda node: (node["District"]+','+node['State']
                    ) == selected_district, district_stats_data))

    if not district_data :
        raise Exception(f"District data not found for selected state: {selected_district}")
    district_data = district_data[0]

    district_graph = plot_graph(district_data["I"], district_data["R"], district_data["hospitalized"],
                                district_data["fatal"], district_data["Rt"], district_data["Date Announced"],
                                district_data["cumsum"], selected_district.split(',')[0])

    return district_graph, state_graph, options


# @app.server.route('/download_global/')
# def download_global():
#     data = json.dumps(global_dict)
#     buffer = BytesIO()
#     buffer.write(data.encode())
#     buffer.seek(0)
#     return send_file(buffer,
#                      attachment_filename='config.json',
#                      as_attachment=True)

# @app.server.route('/download_nodal/')
# def download_nodal():
#     data = json.dumps(node_config_list)
#     buffer = BytesIO()
#     buffer.write(data.encode())
#     buffer.seek(0)
#     return send_file(buffer,
#                      attachment_filename='config.json',
#                      as_attachment=True)

if __name__ == '__main__':
    download_from_aws()
    district_stats_data = get_district_stats()
    state_stats_data = get_state_stats()
    app.run_server()
