from core.seir import network_epidemic_calc
from core.scrap import district_stats_list
from visuals.map import map, day_count
import dash_core_components as dcc
import dash_html_components as html


map_dropdown =     html.Div(
        id="district-dropdown-parent",
        children=[
            dcc.Dropdown(
                id="districtList",
                style={"width": 250},
                options=[
                    {"label": node["District"].upper(), "value": node["District"]}
                    for node in district_stats_list
                ],
                value=district_stats_list[0]["District"],
                searchable=True,
            )
        ],
    )


map_column = html.Div(id="selectors", children=[
    html.H3("Covid-19 India SEIR Model"),
    dcc.Graph(id='map', figure=map,config={'displayModeBar': False},
              style={'width': '100%', 'height': '100%', 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}}),
    html.Div(children=[
        html.A("Global Dict", href="/download_global/"),
        html.A("Nodal Dict", href="/download_nodal/",style={'margin':10}),
        # html.A("Optimize Config", href="/optimize_config/",style={'margin':10}),
        html.Button('Optimize config', id='optimize', n_clicks=0),

    ])
    # ,
    # dcc.Upload(
    #     id="upload-data",
    #     children=html.Div(
    #         ["Drag and dropa Config file to upload and refresh after 30s"]
    #     ),
    #     style={
    #         "width": "100%",
    #         "height": "60px",
    #         "lineHeight": "60px",
    #         "borderWidth": "1px",
    #         "borderStyle": "dashed",
    #         "borderRadius": "5px",
    #         "textAlign": "center",
    #         "margin": "10px",
    #     },
    #     multiple=False,
    # )
])

graph_column = html.Div(id="plots",children=[
    dcc.Graph(id="seir", figure=network_epidemic_calc("India")),
    dcc.Graph(id="seir2", figure=network_epidemic_calc("India"))
])
