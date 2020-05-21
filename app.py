import base64
import json
import threading
from io import BytesIO
import dash
from dash.dependencies import State, Input, Output
from flask import send_file
from core.seir import network_epidemic_calc, plot_graph
from core.scrap import node_config_list, global_dict, get_global_dict, get_nodal_config, modify_optimize_param_flag
import dash_core_components as dcc
import dash_html_components as html
from visuals.vcolumn import map_column, graph_column, map_dropdown

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
    [Input("map", "clickData"), Input("districtList", "value")],
    [State("seir", "figure")], )
def update_time_series(map_click, selected_district, sort_by, city):
    from core.scrap import state_stats_list, district_stats_list
    options = []
    sort_by = "Rt"

    current_node = map_click["points"][0]["text"] if map_click else "India"
    state_data = list(filter(lambda node: node["State"] == current_node, state_stats_list))
    if not state_data:
        raise Exception(f"Data not found for selected state: {current_node}")

    state_data = state_data[0]
    state_graph = plot_graph(state_data["I"], state_data["R"], state_data["hospitalized"],
                             state_data["fatal"], state_data["Rt"], state_data["Date Announced"],
                             state_data["cumsum"], current_node)

    if not map_click:
        return state_graph, state_graph, []

    district_list_of_selected_state = list(filter(lambda node: node["State"] == current_node, district_stats_list))
    district_list_of_selected_state.sort(key=lambda x: x[sort_by], reverse=True)
    options = [{"label": f"{node['District'].upper()} ({node['Rt']})", "value": node["District"]} for node in district_list_of_selected_state]

    selected_district = selected_district if selected_district else options[0]["value"]
    district_data = list(filter(lambda node: node["District"] == selected_district, district_stats_list))

    if not district_data :
        raise Exception(f"District data not found for selected state: {selected_district}")
    district_data = district_data[0]

    district_graph = plot_graph(district_data["I"], district_data["R"], district_data["hospitalized"],
                                district_data["fatal"], district_data["Rt"], district_data["Date Announced"],
                                district_data["cumsum"], selected_district)

    return district_graph, state_graph, options


# @app.callback(
#     Output("seir2", "figure"),
#     [Input("upload-data", "filename"), Input("upload-data", "contents")],
# )
# def update_output(uploaded_filenames, config_file):
#     default_return = network_epidemic_calc("India")
#     if config_file is not None:
#         config_file = json.loads(base64.b64decode(config_file[28:]).decode('utf-8'))
#         if type(config_file) == list:
#             get_nodal_config(config_file)
#         else :
#             get_global_dict(config_file)

#         network_epidemic_calc.memo={}
#         thread = threading.Thread(target=network_epidemic_calc, args=["India"])
#         thread.daemon = True
#         thread.start()
#     return default_return

@app.server.route('/download_global/')
def download_global():
    data = json.dumps(global_dict)
    buffer = BytesIO()
    buffer.write(data.encode())
    buffer.seek(0)
    return send_file(buffer,
                     attachment_filename='config.json',
                     as_attachment=True)

@app.server.route('/download_nodal/')
def download_nodal():
    data = json.dumps(node_config_list)
    buffer = BytesIO()
    buffer.write(data.encode())
    buffer.seek(0)
    return send_file(buffer,
                     attachment_filename='config.json',
                     as_attachment=True)

if __name__ == '__main__':
    app.run_server()
