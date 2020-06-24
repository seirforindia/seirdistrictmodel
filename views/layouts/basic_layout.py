import dash_core_components as dcc
import dash_html_components as html
from views.plots.map_plot import MapPlot

DATA_DIR = 'data'
STATE_STATS = 'state_stats.json'
DISTRICT_STATS = 'district_stats.json'

class Layout:

    def graph_column_layout(self):
        map_dropdown = html.Div(
            id="district-dropdown-parent",
            children=[
                html.Div(children=[html.Div("Choose District", style={"font-weight": "bold"})]),
                dcc.RadioItems(
                    id="sort-by",
                    options=[
                        {'label': 'R(t)', 'value': 'Rt'},
                        {'label': 'Hospital beds needed (30 days)', 'value': 'hospitalized'},
                    ],
                    value='hospitalized',
                    labelStyle={'display': 'inline-block'}
                ),
                dcc.Dropdown(
                    id="districtList",
                    style={"width": 250},
                    searchable=True,
                )
            ],
            style={"border-style": "bold"}
        )


        graph_column = html.Div(id="plots",children=[
            map_dropdown,
            dcc.Graph(id="seir"),
            dcc.Graph(id="seir2")
        ])

        return graph_column

    def map_columns_layout(self):
        return html.Div(id="selectors", children=[
            html.H3("iSPIRT India COVID-19 SEIR Model"),
            html.A(children=html.Button(children='Home : India level Predictions'), href='https://indiadistrictmodel.indiacovidmodel.in/', className='btn btn-default', style={'background-color':'white'}),
            dcc.Graph(id='map', figure=MapPlot().plot(),config={'displayModeBar': False},
                      style={'width': '100%', 'height': '85%', 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}}),
            html.A(children=html.Button(children='Create your own model'), href='https://diymodel.indiacovidmodel.in/',  className='btn btn-default', style={'backgroundColor':'white'}),
            html.A(children=html.Button(children='Click here for model specifications'), href='https://indiacovidmodel.in/',  className='btn btn-default', style={'backgroundColor':'white'}),
            html.Div(children=[
                html.P(u'iSPIRT India COVID-19 SEIR MODEL is an open source project managed by ',  style={'margin-top': '48px', 'font-size': '14px', 'float':'left'}),
            ]),
            html.A([html.Img(src=('https://ispirt.in/wp-content/themes/ispirt/img/isprit_logo.svg'), style={'margin-top': '25px','float':'left','height':'7%', 'width':'7%'})], href='https://ispirt.in'),
            html.Div(children=[
                html.P(u' || Supported by ',  style={'margin-top': '50px', 'font-size': '14px', 'float':'left'}),
            ]),
            html.A([html.Img(src=('https://www.thoughtworks.com/imgs/tw-logo.svg'), style={'margin-top': '17px','float':'left','height':'9%', 'width':'9%'})],href='https://www.thoughtworks.com'),
            html.Div(children=[
                html.P('All data has been sourced from ',  style={'margin-top': '0px', 'font-size': '14px', 'float':'left'}),
            ]),
            html.B(children=[html.A('covid19india.org', href="https://api.covid19india.org/", style={'margin-top': '0px', 'margin-left': '5px', 'font-size': '14px', 'float':'left'})]),
            html.Div(html.P(['', html.Br(), ''])),
        ])

    def base_layout(self):
        return html.Div(
            children=[
                html.Div(id="covidapp", className="two columns",
                         children=dcc.Loading(
                             children=[html.Div(id="dropdown-select-outer",
                                                children=[self.map_columns_layout(), self.graph_column_layout()]
                                                )]
                         )
                         )
            ], style= {"padding":0,"margin":0}
        )
