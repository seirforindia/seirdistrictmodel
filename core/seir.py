import random
import plotly.graph_objects as go
import numpy as np
from operator import itemgetter
import json
import datetime
import copy
import _pickle as cPickle
import pandas as pd
from core.scrap import states,states_series,global_dict,node_config_list
# import core.scrap as core_scrap
from visuals.layouts import get_bar_layout
from core.configuration import *

CFR_div=1
I_mult=1
rate_range=[0,1]
I_range=[0,200]

def plot_graph(T, I, R, Severe_H, R_Fatal, interventions, city):
    days = (datetime.datetime.now() - datetime.datetime(2020,1,1,0,0,0,0)).days
    low_offset = -30
    high_offset = 30
    ht = '''%{fullData.name}	<br> &#931; :%{y:}<br> &#916;: %{text}<br> Day :%{x} <extra></extra>'''
    ht_active = '''%{fullData.name}	<br> &#931; :%{y:}<br> Day :%{x} <extra></extra>'''
    active = I[days+low_offset:days+high_offset].astype(int)
    trace1 = go.Scatter(x=T[days+low_offset:days+high_offset], y=active ,name='Active Infectious', text=np.diff(active),
                    marker=dict(color='rgb(253,192,134,0.2)'), hovertemplate=ht)
    total=I[days+low_offset:days+high_offset].astype(int)+R[days+low_offset:days+high_offset].astype(int)
    trace2 = go.Scatter(x=T[days+low_offset:days+high_offset], y=total , name='Total Infected', text=total,
                    marker=dict(color='rgb(240,2,127,0.2)'), hovertemplate=ht_active)
    severe=Severe_H[days+low_offset:days+high_offset].astype(int)
    trace3 = go.Scatter(x=T[days+low_offset:days+high_offset], y=severe,name='Hospitalized', text=np.diff(severe),
                    marker=dict(color='rgb(141,160,203,0.2)'), hovertemplate=ht)
    fatal=R_Fatal[days+low_offset:days+high_offset].astype(int)
    trace4 = go.Scatter(x=T[days+low_offset:days+high_offset], y=fatal, name='Fatalities', text=np.diff(fatal),
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
                    marker=dict(color='rgb(0,0,0,0.2)'), hovertemplate=ht_active)

    data = [trace1, trace2, trace3, trace4, trace5]

    for intervention in interventions:
        if (city == "India" and intervention["intervention_type"] == "global") or city != "India":
            hover_text = ""
            for key, value in intervention.items():
                hover_text += str(key) + ' : ' + str(value) + '<br>'
            intervention_date=datetime.datetime(2020,1,1) + datetime.timedelta(days=int(intervention["intervention_day"]))
            it = go.Scatter(y=[0, (max(I[days-30:days+30]+max(R[days-30:days+30])))/2],
                            x=[intervention_date, intervention_date],
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

def add_optimize_param_to_config(local_config, node_config, tn):
    intial_jump,jump,delay=5,5,5
    ts = states_series[states_series.States==local_config["node"]].reset_index()
    ts["Date Announced"] = pd.to_datetime(ts["Date Announced"])
    latest_day=int((ts['Date Announced'][len(ts)-1]-datetime.datetime(2020,1,1,0,0,0,0)).days)+1
    new_param=[]
    node_config.param=new_param
    for d in range(intial_jump+tn,latest_day-jump+1,jump):
        period=jump if d+jump*2<=latest_day else latest_day-d
        ratefrac=optimize_param(node_config,"rate_frac",d+period,rate_range,period)
        print('Opt rate frac:',ratefrac,'@',d-delay)
        rate_frac_opt=np.array([ratefrac]*4)        
        new_param.append({"intervention_day":d-delay,"rate_frac":rate_frac_opt})
        node_config.param=new_param
        I_opt=optimize_param(node_config,"I0",d+period,I_range,period)
        if abs(I_opt-np.sum(node_config.I0))>2:
            node_config.I0=np.round(I_opt*node_config.pop_frac)
            node_config.E0=np.round(1.5*I_opt*node_config.pop_frac)
            print('//  Opt I0:',I_opt)

    node_config = SeirConfig(nodal_config=local_config,global_config=global_dict)
    try:
        node_config.I0=np.round(I_opt*node_config.pop_frac)
        node_config.E0=np.round(1.5*node_config.I0)
        node_config.param=new_param
        print("Changable Parameters list on intervention for this node :  ",node_config.param)
    except:
        node_config.I0=np.round(50*node_config.pop_frac)
        node_config.E0=np.round(1.5*node_config.I0)
    return node_config

def unmemoized_network_epidemic_calc(city, days=200):
    from core.scrap import node_config_list,global_dict, optimize_param_flag, modify_optimize_param_flag
    print('inside seir:optimise param', optimize_param_flag)
    I, R, Severe_H, R_Fatal = np.array([0] * days), np.array([0] * days), np.array([0] * days), np.array([0] * days)
    if city == "India":
        for local_config in node_config_list:
            node_config = SeirConfig(nodal_config=local_config,global_config=global_dict)
            tn=node_config.t0
            if optimize_param_flag:
                node_config = add_optimize_param_to_config(local_config, node_config, tn)
            # import local params json file to instantiate objects
            
            node_config.getSolution(days)
            I = I + [np.sum(i) for i in node_config.I]
            R = R+ [np.sum(i) for i in node_config.R]
            Severe_H = Severe_H+ [np.sum(i) for i in node_config.Severe_H]
            R_Fatal = R_Fatal+ [np.sum(i) for i in node_config.R_Fatal]
    else:
        local_config="Gujarat"
        for obj in node_config_list:
            if obj["node"]==city:
                local_config = obj
        node_config = SeirConfig(nodal_config=local_config,global_config=global_dict)
        tn = node_config.t0
        if optimize_param_flag:
            node_config = add_optimize_param_to_config(local_config, node_config, tn)
        
        node_config.getSolution(days)
        I = I + [np.sum(i) for i in node_config.I]
        R = R+ [np.sum(i) for i in node_config.R]
        Severe_H = Severe_H+ [np.sum(i) for i in node_config.Severe_H]
        R_Fatal = R_Fatal+ [np.sum(i) for i in node_config.R_Fatal]
    T = np.array([(datetime.datetime(2020,1,1) + datetime.timedelta(days=i)) for i in range(days)])
    # change optimize param to normal scenario value (False)
    modify_optimize_param_flag(False)
    return plot_graph(T, I, R, Severe_H, R_Fatal,node_config.param +[{"intervention_day":tn,"intervention_type":"T50"}], city)

def slope_calc(a):
    i,slope=0,[]
    while i < len(a)-2:
        slope.append((a[i+2]-a[i])/2)
        i+=1
    return np.array(slope)

def rms_cal(value,nodal_config,key,t,match_period):
    if key=="I0":
        new_dict={"I0":np.round(value*np.array(nodal_config.pop_frac)),"E0":np.round(1.5*value*np.array(nodal_config.pop_frac))}
    elif key=="rate_frac":
        a=nodal_config.param
        b=[{"intervention_day":t-match_period-5,key:np.array([value]*4)}]
        param_val=a+b
        new_dict={"param":param_val}
    else:
        new_dict={key:value}
    temp_con=copy.copy(nodal_config)
    temp_con.__dict__.update(new_dict)
    temp_con.getSolution(t)
    I = np.array([np.sum(i) for i in temp_con.I])
    R = np.array([np.sum(i) for i in temp_con.R])
    I_pred=(I+R)[t-match_period:t] if key!='rate_frac' else slope_calc((I+R)[t-match_period:t])
    ts = states_series[states_series.States==nodal_config.node].reset_index()
    ts["Date Announced"] = pd.to_datetime(ts["Date Announced"])
    ts["Patient Number"] = ts["Patient Number"].cumsum()
    I_cal = ts[ts["Date Announced"] <= datetime.datetime(2020,1,1,0,0,0,0)+ datetime.timedelta(days=t-1)]
    I_real=list(I_cal[-match_period:]['Patient Number']) if key!='rate_frac' else slope_calc(list(I_cal[-match_period:]['Patient Number']))
    I_dist=(I_pred/I_mult)-(np.array(I_real))
    rms_dist=np.sqrt(np.mean(I_dist*I_dist))
    return rms_dist


def optimize_param(node1_local_config,key,today,p_range=[0,100],match_period=7):
    min_val=p_range[0]
    max_val=p_range[1]
    thresh=0.05 if key=="rate_frac" else 4
    while True:
        mid_val=(min_val+max_val)/2 if key=="rate_frac" else int((min_val+max_val)/2) 
        if abs(min_val-max_val)<thresh:
            if rms_cal(mid_val,node1_local_config,key,today,match_period)>rms_cal(min_val,node1_local_config,key,today,match_period):
                return min_val
            elif rms_cal(mid_val,node1_local_config,key,today,match_period)>rms_cal(max_val,node1_local_config,key,today,match_period):
                return max_val
            else:
                return mid_val
        elif rms_cal(mid_val,node1_local_config,key,today,match_period)>rms_cal(mid_val-thresh/2,node1_local_config,key,today,match_period):
            max_val=mid_val
        else:
            min_val=mid_val


network_epidemic_calc = MemoizeMutable(unmemoized_network_epidemic_calc)
