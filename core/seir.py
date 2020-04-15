import random
import plotly.graph_objects as go
import numpy as np
from operator import itemgetter
import json
import datetime
import _pickle as cPickle
import pandas as pd
from core.scrap import states,states_series
from visuals.layouts import get_bar_layout
from core.configuration import *
import csv
import json

node_config_list=[]
with open('data/nodal.json') as g :
    nodes = json.load(g)
    for node in nodes:
        if node["node"] in states.States.to_list():
            node_config_list.append(states.loc[states.States==node["node"],["States","Population","TN"]]. \
                                  rename(columns ={"States":"node","Population":"pop","TN":"t0"}).to_dict('r')[0])


def plot_graph(T, I, R, Severe_H, R_Fatal, interventions, city):
    days = (datetime.datetime.now() - datetime.datetime(2020,1,1,0,0,0,0)).days
    low_offset = -30
    high_offset = 20
    ht = '''%{fullData.name}	<br> &#931; :%{y:}<br> &#916;: %{text}<br> Day :%{x:} <extra></extra>'''
    active = I[days+low_offset:days+high_offset].astype(int)
    trace1 = go.Scatter(x=T[days+low_offset:days+high_offset], y=active ,name='Active Infectious &nbsp;', text=np.diff(active),
                    marker=dict(color='rgb(253,192,134,0.2)'), hovertemplate=ht)
    total=I[days+low_offset:days+high_offset].astype(int)+R[days+low_offset:days+high_offset].astype(int)
    trace2 = go.Scatter(x=T[days+low_offset:days+high_offset], y=total , name='Total Infected &nbsp; &nbsp; &nbsp; &nbsp;', text=total,
                    marker=dict(color='rgb(240,2,127,0.2)'), hovertemplate=ht)
    severe=Severe_H[days+low_offset:days+high_offset].astype(int)
    trace3 = go.Scatter(x=T[days+low_offset:days+high_offset], y=severe,name='Hospitalized  &nbsp; &nbsp; &nbsp; &nbsp;', text=np.diff(severe),
                    marker=dict(color='rgb(141,160,203,0.2)'), hovertemplate=ht)
    fatal=R_Fatal[days+low_offset:days+high_offset].astype(int)
    trace4 = go.Scatter(x=T[days+low_offset:days+high_offset], y=fatal, name='Fatalities &nbsp;&nbsp; &nbsp;&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;', text=np.diff(fatal),
                    marker=dict(color='rgb(56,108,176,0.2)'), hovertemplate=ht)

    if city=="India":
        ts = states_series.groupby("Date Announced",as_index=False)["Patient Number"].sum().reset_index()
    else :
        ts = states_series[states_series.States==city].groupby("Date Announced",as_index=False)["Patient Number"].sum().reset_index()

    ts["Date Announced"] = pd.to_datetime(ts["Date Announced"]).dt.date
    r = pd.date_range(start=ts["Date Announced"].min(), end =datetime.datetime.now().date())
    ts = ts.set_index("Date Announced").reindex(r).fillna(0).rename_axis("Date Announced").reset_index()
    ts["Patient Number"] = ts["Patient Number"].cumsum()
    filter = ts["Date Announced"].dt.date >= datetime.datetime.now().date()- datetime.timedelta(days=-low_offset)
    y_actual = [0]*(-low_offset - len(ts[filter]["Patient Number"])) + list(ts[filter]["Patient Number"])
    trace5 = go.Scatter(x=T[days+ low_offset:days], y=y_actual , name='Actual Infected &nbsp; &nbsp;', text=total,
                    marker=dict(color='rgb(0,0,0,0.2)'), hovertemplate=ht)

    data = [trace1, trace2, trace3, trace4, trace5]

    for intervention in interventions:
        if (city == "India" and intervention["intervention_type"] == "global") or city != "India":
            hover_text = ""
            for key, value in intervention.items():
                hover_text += str(key) + ' : ' + str(value) + '<br>'
            it = go.Scatter(y=[0, (max(I[days-30:days+20]+max(R[days-30:days+20])))/2],
                            x=[intervention["intervention_day"], intervention["intervention_day"]],
                            mode='lines',
                            showlegend=False,
                            text=hover_text,
                            hoverinfo="text",marker=dict(color='rgb(0,0,0,0.2)'))
            data.append(it)

    layout = get_bar_layout(city)

    return {"data": data[::-1], "layout": layout}

class MemoizeMutable:
    def __init__(self, fn):
        self.fn = fn
        self.memo = {}
    def __call__(self, *args, **kwds):
        str = cPickle.dumps(args, 1)+cPickle.dumps(kwds, 1)
        if not str in self.memo:
            self.memo[str] = self.fn(*args, **kwds)
        return self.memo[str]

### todo : when we start using config files to make realtime modification this function must take in the config file or its version as parameter
def unmemoized_network_epidemic_calc(city, days=200):
    I, R, Severe_H, R_Fatal = np.array([0] * days), np.array([0] * days), np.array([0] * days), np.array([0] * days)
    if city == "India":
        for local_config in node_config_list:
            node_config = SeirConfig(nodal_config=local_config)
            tn=node_config.t0
            # import local params json file to instantiate objects
            node_config.getSolution(days)
            I = I + [np.sum(i) for i in node_config.I]
            R = R+ [np.sum(i) for i in node_config.R]
            Severe_H = Severe_H+ [np.sum(i) for i in node_config.Severe_H]
            R_Fatal = R_Fatal+ [np.sum(i) for i in node_config.R_Fatal]
    else:
        local_config = next(obj for obj in node_config_list  if obj["node"]==city)
        node_config = SeirConfig(nodal_config=local_config)
        tn = node_config.t0
        node_config.getSolution(days)
        I = I + [np.sum(i) for i in node_config.I]
        R = R+ [np.sum(i) for i in node_config.R]
        Severe_H = Severe_H+ [np.sum(i) for i in node_config.Severe_H]
        R_Fatal = R_Fatal+ [np.sum(i) for i in node_config.R_Fatal]

    return plot_graph(np.arange(days) + 1, I, R, Severe_H, R_Fatal,node_config.param +[{"intervention_day":tn,"intervention_type":"T50"}], city)

network_epidemic_calc = MemoizeMutable(unmemoized_network_epidemic_calc)


