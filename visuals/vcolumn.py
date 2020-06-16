import numpy as np
import pandas as pd
import datetime
import plotly.graph_objects as go

from visuals.map import map, day_count
from visuals.layouts import get_bar_layout
import dash_core_components as dcc
import dash_html_components as html
from core.file_locator import FIRSTJAN

map_dropdown = html.Div(
        id="district-dropdown-parent",
        children=[
            html.Div(children=[html.Div("Choose District", style={"font-weight": "bold"})]),
            dcc.RadioItems(
                id="sort-by",
                options=[
                    {'label': 'R(t)', 'value': 'Rt'},
                    {'label': 'Critical hospitalized count', 'value': 'hospitalized'},
                ],
                value='cumsum',
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


map_column = html.Div(id="selectors", children=[
    html.H3("iSPIRT India COVID-19 SEIR Model"),
    html.A(children=html.Button(children='Home : India level Predictions'), href='/', className='btn btn-default', style={'background-color':'white'}),
    dcc.Graph(id='map', figure=map,config={'displayModeBar': False},
              style={'width': '100%', 'height': '85%', 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}}),
    html.A(children=html.Button(children='Click here for model specifications'), href='https://indiacovidmodel.in/',  className='btn btn-default', style={'backgroundColor':'white'}),
    html.Div(children=[
        html.P(u"\u00A9"+ 'Developed by ',  style={'margin-top': '48px', 'font-size': '14px', 'float':'left'}),
    ]),
    html.A([html.Img(src=('https://ispirt.in/wp-content/themes/ispirt/img/isprit_logo.svg'), style={'margin-top': '30px','float':'left','height':'7%', 'width':'7%'})], href='https://ispirt.in'),
    html.Div(children=[
        html.P(u' || Supported by ',  style={'margin-top': '50px', 'font-size': '14px', 'float':'left'}),
    ]),
    html.A([html.Img(src=('https://www.thoughtworks.com/imgs/tw-logo.svg'), style={'margin-top': '20px','float':'left','height':'9%', 'width':'9%'})],href='https://www.thoughtworks.com'),
    html.Div(children=[
        html.P(' ||           All data has been sourced from ',  style={'margin-top': '50px', 'font-size': '14px', 'float':'left'}),
    ]),
    html.B(children=[html.A('covid19india.org', href="https://api.covid19india.org/", style={'margin-top': '50px', 'margin-left': '5px', 'font-size': '14px', 'float':'left'})]),
    html.Div(html.P(['', html.Br(), ''])),
    #  html.Div(children=[
    #      html.A("Global Dict", href="/download_global/"),
    #      html.A("Nodal Dict", href="/download_nodal/",style={'margin':10}),
    #      # html.A("Optimize Config", href="/optimize_config/",style={'margin':10}),
    #      #  html.Button('Optimize config', id='optimize', n_clicks=0),
    #
    #  ])
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
    map_dropdown,
    dcc.Graph(id="seir"),
    dcc.Graph(id="seir2")
])


def plot_graph(I, R, Severe_H, R_Fatal, rate_frac, date, cumsum, mt, node, test_per=0):
    I = np.array([int(n) for n in I])
    R = np.array([int(n) for n in R])
    Severe_H = np.array([int(n) for n in Severe_H])
    R_Fatal = np.array([int(n) for n in R_Fatal])

    T = np.array([(FIRSTJAN + datetime.timedelta(days=i)) for i in range(241)])
    days = (datetime.datetime.now() - FIRSTJAN).days
    low_offset = -30
    high_offset = 35
    ht_delta = '''%{fullData.name}	<br> &#931; :%{y:,}<br> &#916;: %{text}<br> Day :%{x} <extra></extra>'''
    ht_active = '''%{fullData.name}	<br> &#931; :%{y:,}<br> Day :%{x} <extra></extra>'''
    active = I[days+low_offset:days+high_offset]
    trace1 = go.Scatter(x=T[days+low_offset:days+high_offset], y=active ,name='Active Infectious', text=np.diff(active),
                    marker=dict(color='rgb(253,192,134,0.2)'), hovertemplate=ht_active)
    total=I[days+low_offset:days+high_offset]+R[days+low_offset:days+high_offset]
    trace2 = go.Scatter(x=T[days+low_offset:days+high_offset], y=total , name='Predicted Infected', text=total,
                    marker=dict(color='rgb(240,2,127,0.2)'), hovertemplate=ht_active)

    severe=Severe_H[days+low_offset:days+high_offset]
    trace3 = go.Scatter(x=T[days+low_offset:days+high_offset], y=severe,name='Critical hospitalized', text=np.diff(severe),
                    marker=dict(color='rgb(141,160,203,0.2)'), hovertemplate=ht_active)
    fatal=R_Fatal[days+low_offset-15:days+high_offset-15]
    trace4 = go.Scatter(x=T[days+low_offset:days+high_offset], y=fatal, name='Fatalities', text=np.diff(fatal),
                    marker=dict(color='rgb(56,108,176,0.2)'), hovertemplate=ht_active)

    date = pd.to_datetime(date, format='%Y-%m-%d').date
    ts = pd.DataFrame({"Date Announced":date, "cumsum":cumsum})
    # r = pd.date_range(start=start_date, end =ts['Date Announced'].max())
    # ts = ts.set_index("Date Announced").reindex(r).fillna(0).rename_axis("Date Announced").reset_index()
    r = pd.date_range(start=ts['Date Announced'].min(), end =datetime.datetime.now().date())
    lastValue = list(ts['cumsum'])[-1]
    ts = ts.set_index("Date Announced").reindex(r).fillna(lastValue).rename_axis("Date Announced").reset_index()
    filter = ts["Date Announced"].dt.date >= datetime.datetime.now().date()- datetime.timedelta(days=-low_offset)
    y_actual = [0]*(-low_offset - len(ts[filter]["cumsum"])) + list(ts[filter]["cumsum"])

    trace5 = go.Scatter(x=T[days+ low_offset:days], y=y_actual , name='Reported Infected &nbsp; &nbsp;', text=total,
                    marker=dict(color='rgb(0,0,0,0.2)'), hovertemplate=ht_active)

    data = [trace1, trace2, trace3, trace4, trace5]

    # find infected and Fatal after 15 and 30 days
    all_dates = [i.date() for i in T]
    today = datetime.date.today()
    dateAfter15days = today+datetime.timedelta(days=15)
    dateAfter30days = today+datetime.timedelta(days=30)
    today = today-datetime.timedelta(days=1)
    todayIndex = all_dates.index(today)
    indexAfter15day = all_dates.index(dateAfter15days)
    indexAfter30day = all_dates.index(dateAfter30days)

    textToday =  ["", today.strftime("%d %b")+',<br>Infected : {:,}'.format((I[todayIndex]+R[todayIndex])) + '<br>'\
                  +'Fatal : {:,}<br>Hospitalized : {:,}'.format(R_Fatal[todayIndex-15],Severe_H[todayIndex])]
    barAtToday = go.Scatter(y=[0, (max(I[days+low_offset:days+high_offset])+max(R[days+low_offset:days+high_offset]))/1.5],
                            x=[T[todayIndex], T[todayIndex]],
                            mode='lines+text',
                            showlegend=False,
                            text=textToday,
                            textfont_size=12,
                            line=dict(dash='dash', width=1,color='black'),
                            textposition="top left",hoverinfo="none")
    data.append(barAtToday)
    
    textAt15day =  ["", dateAfter15days.strftime("%d %b")+',<br>Infected : {:,}'.format((I[indexAfter15day]+R[indexAfter15day])) + '<br>'\
                  +'Fatal : {:,}<br>Hospitalized : {:,}'.format(R_Fatal[indexAfter15day-15],Severe_H[indexAfter15day])]
    barAt15day = go.Scatter(y=[0, (max(I[days+low_offset:days+high_offset])+max(R[days+low_offset:days+high_offset]))/1.5],
                            x=[T[indexAfter15day], T[indexAfter15day]],
                            mode='lines+text',
                            showlegend=False,
                            text=textAt15day,
                            textfont_size=12,
                            line=dict(dash='dash', width=1,color='black'),
                            textposition="top left",hoverinfo="none")
    data.append(barAt15day)
    textAt30day = ["", dateAfter30days.strftime("%d %b")+',<br>Infected : {:,}'.format(I[indexAfter30day]+R[indexAfter30day]) + '<br>'\
                +'Fatal : {:,}<br>Hospitalized : {:,}'.format(R_Fatal[indexAfter30day-15],Severe_H[indexAfter30day])]
    barAt30day = go.Scatter(y=[0, (max(I[days+low_offset:days+high_offset])+max(R[days+low_offset:days+high_offset]))/1.5],
                            x=[T[indexAfter30day], T[indexAfter30day]],
                            mode='lines+text',
                            showlegend=False,
                            text=textAt30day,
                            textfont_size=12,
                            line=dict(dash='dash', width=1, color='black'),
                            textposition="top left",hoverinfo="none")
    data.append(barAt30day)

    layout = get_bar_layout(node, rate_frac, mt, test_per)

    return {"data": data[::-1], "layout": layout}
