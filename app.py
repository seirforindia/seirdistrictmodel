import base64
import json
import threading
from io import BytesIO
import dash
from dash.dependencies import State, Input, Output
from flask import send_file
from core.seir import network_epidemic_calc, plot_graph
from core.scrap import node_config_list, global_dict, get_global_dict, get_nodal_config, modify_optimize_param_flag, district_stats_list, state_stats_list
import dash_core_components as dcc
import dash_html_components as html
from visuals.vcolumn import map_column, graph_column

app = dash.Dash(__name__)
server = app.server

app_layout = html.Div(children=[html.Div(id="covidapp", className="two columns", children=dcc.Loading(
    children=[html.Div(id="dropdown-select-outer", children=[map_column, graph_column])]))], style= {"padding":0,"margin":0})
app.layout = app_layout


@app.callback(
    [Output("seir", "figure"), Output('seir2', 'figure')],
    [Input("map", "clickData"), Input("districtList", "value")],
    [State("seir", "figure")], )
def update_time_series(map_click, selected_district, city):
    selected_district = selected_district if selected_district else "agra"
    data1 = list(filter(lambda node: node["District"] == selected_district, district_stats_list))[0]
    #  city = city["layout"]["title"]["text"].split(" ")[-1]
    #  return network_epidemic_calc(city)
    graph1 = plot_graph(data1["I"], data1["R"], data1["hospitalied"], data1["fatal"], data1["Rt"], data1["Date Announced"], data1["numcases"], selected_district)

    current_node = map_click["points"][0]["text"] if map_click else "Uttar Pradesh"
    #  current_node = current_node if current_node else "Maharashtra"
    #  return network_epidemic_calc(current_node)
    data2 = list(filter(lambda node: node["State"] == current_node, state_stats_list))[0]

    graph2 = plot_graph(data2["I"], data2["R"], data2["hospitalied"], data2["fatal"], data2["Rt"], data2["Date Announced"], data2["numcases"], current_node)

    return graph1, graph2


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

#  @app.callback(
#      [Output('seir2', 'figure'),
#       Output('optimize', 'disabled')],
#      [Input('optimize', 'n_clicks')])
#  def optimize_param(n_clicks):
#      default_return = network_epidemic_calc("India")
#      print('button clicked: ',n_clicks)
#      from core.scrap import optimize_param_flag
#
#      if n_clicks == 1 and not optimize_param_flag:
#          default_return = network_epidemic_calc("India")
#          modify_optimize_param_flag(True)
#          # print('I am executing..')
#          network_epidemic_calc.memo={}
#          thread = threading.Thread(target=network_epidemic_calc, args=["India"])
#          thread.daemon = True
#          thread.start()
#          return default_return, True
#      return default_return, False


# def optimize_config():
    # modify_optimize_param_flag(True)
    # network_epidemic_calc.memo={}
    # thread = threading.Thread(target=network_epidemic_calc, args=["India"])
    # thread.daemon = True
    # thread.start()
    # return "Optimizer running in backgroun , please go back to previous page and refresh after few hours"


if __name__ == '__main__':
    app.run_server()
