import random
import plotly.graph_objects as go
import numpy as np
from operator import itemgetter
import json
import datetime
import copy
import _pickle as cPickle
import pandas as pd
from core.scrap import states_series, global_dict, node_config_list, FIRSTJAN, prepare_age_wise_estimation, district_series, district_node_config
# import core.scrap as core_scrap
from visuals.layouts import get_bar_layout
from core.configuration import *

CFR_div=1
I_mult=1
rate_range=[0,1]
I_range=[0,2500]

def plot_graph(I, R, Severe_H, R_Fatal, rate_frac, date, cumsum, node):
    I = np.array([int(n) for n in I])
    R = np.array([int(n) for n in R])
    Severe_H = np.array([int(n) for n in Severe_H])
    R_Fatal = np.array([int(n) for n in R_Fatal])

    T = np.array([(FIRSTJAN + datetime.timedelta(days=i)) for i in range(241)])
    days = (datetime.datetime.now() - FIRSTJAN).days
    low_offset = -30
    high_offset = 35
    ht = '''%{fullData.name}	<br> &#931; :%{y:,}<br> &#916;: %{text}<br> Day :%{x} <extra></extra>'''
    ht_active = '''%{fullData.name}	<br> &#931; :%{y:,}<br> Day :%{x} <extra></extra>'''
    active = I[days+low_offset:days+high_offset]
    trace1 = go.Scatter(x=T[days+low_offset:days+high_offset], y=active ,name='Active Infectious', text=np.diff(active),
                    marker=dict(color='rgb(253,192,134,0.2)'), hovertemplate=ht)
    total=I[days+low_offset:days+high_offset]+R[days+low_offset:days+high_offset]
    trace2 = go.Scatter(x=T[days+low_offset:days+high_offset], y=total , name='Total Infected', text=total,
                    marker=dict(color='rgb(240,2,127,0.2)'), hovertemplate=ht_active)
    severe=Severe_H[days+low_offset:days+high_offset]
    trace3 = go.Scatter(x=T[days+low_offset:days+high_offset], y=severe,name='Hospitalized', text=np.diff(severe),
                    marker=dict(color='rgb(141,160,203,0.2)'), hovertemplate=ht)
    fatal=R_Fatal[days+low_offset:days+high_offset]
    trace4 = go.Scatter(x=T[days+low_offset:days+high_offset], y=fatal, name='Fatalities', text=np.diff(fatal),
                    marker=dict(color='rgb(56,108,176,0.2)'), hovertemplate=ht)

    date = pd.to_datetime(date, format='%Y-%m-%d').date
    ts = pd.DataFrame({"Date Announced":date, "cumsum":cumsum})
    r = pd.date_range(start=ts['Date Announced'].min(), end =datetime.datetime.now().date())
    ts = ts.set_index("Date Announced").reindex(r).fillna(0).rename_axis("Date Announced").reset_index()
    filter = ts["Date Announced"].dt.date >= datetime.datetime.now().date()- datetime.timedelta(days=-low_offset)
    y_actual = [0]*(-low_offset - len(ts[filter]["cumsum"])) + list(ts[filter]["cumsum"])

    trace5 = go.Scatter(x=T[days+ low_offset:days], y=y_actual , name='Actual Infected &nbsp; &nbsp;', text=total,
                    marker=dict(color='rgb(0,0,0,0.2)'), hovertemplate=ht_active)

    data = [trace1, trace2, trace3, trace4, trace5]

    # find infected and Fatal after 15 and 30 days
    all_dates = [i.date() for i in T]
    indexAfter15day = all_dates.index(datetime.date.today()+datetime.timedelta(days=15))
    indexAfter30day = all_dates.index(datetime.date.today()+datetime.timedelta(days=30))

    textAt15day =  ["", 'After 15 days,<br>Infected : {:,}'.format((I[indexAfter15day]+R[indexAfter15day])) + '<br>'\
                  +'Fatal : {:,}'.format((R_Fatal[indexAfter15day]))]
    barAt15day = go.Scatter(y=[0, (max(I[days+low_offset:days+high_offset])+max(R[days+low_offset:days+high_offset]))/2],
                            x=[T[indexAfter15day], T[indexAfter15day]],
                            mode='lines+text',
                            showlegend=False,
                            text=textAt15day,
                            textfont_size=12,
                            line=dict(dash='dash', width=1,color='black'),
                            textposition="top left",hoverinfo="none")
    data.append(barAt15day)
    textAt30day = ["", 'After 30 days,<br>Infected : {:,}'.format(I[indexAfter30day]+R[indexAfter30day]) + '<br>'\
                +'Fatal : {:,}'.format(R_Fatal[indexAfter30day])]
    barAt30day = go.Scatter(y=[0, (max(I[days+low_offset:days+high_offset])+max(R[days+low_offset:days+high_offset]))/2],
                            x=[T[indexAfter30day], T[indexAfter30day]],
                            mode='lines+text',
                            showlegend=False,
                            text=textAt30day,
                            textfont_size=12,
                            line=dict(dash='dash', width=1, color='black'),
                            textposition="top left",hoverinfo="none")
    data.append(barAt30day)

    currR0 = round(rate_frac, 2)
    layout = get_bar_layout(node, currR0)

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

def add_optimize_param_to_config(ts, local_config, node_config, tn):
    intial_jump,jump,delay=5,5,5
    ts["Date Announced"] = pd.to_datetime(ts["Date Announced"])
    latest_day=int((ts['Date Announced'][len(ts)-1]-FIRSTJAN).days)+1
    new_param=[]
    node_config.param=new_param
    print(local_config['node'])
    for d in range(intial_jump+tn,latest_day-jump+1,jump):
        period=jump if d+jump*2<=latest_day else latest_day-d
        ratefrac=optimize_param(ts, node_config,"rate_frac",d+period,rate_range,period)
        print('Opt rate frac:',ratefrac,'@',d-delay)
        rate_frac_opt=np.array([ratefrac]*4)
        new_param.append({"intervention_day":d-delay,"rate_frac":rate_frac_opt})
        node_config.param=new_param
        I_opt=optimize_param(ts, node_config,"I0",d+period,I_range,period)
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

def unmemoized_network_epidemic_calc(data, local_config, days=241):
    from core.scrap import optimize_param_flag, modify_optimize_param_flag
    I, R, Severe_H, R_Fatal = np.array([0] * days), np.array([0] * days), np.array([0] * days), np.array([0] * days)
    node_config = SeirConfig(nodal_config=local_config,global_config=global_dict)
    tn = node_config.t0
    if optimize_param_flag:
        node_config = add_optimize_param_to_config(data, local_config, node_config, tn)
    
    node_config.getSolution(days)
    I = I + [np.sum(i) for i in node_config.I]
    R = R+ [np.sum(i) for i in node_config.R]
    Severe_H = Severe_H+ [np.sum(i) for i in node_config.Severe_H]
    R_Fatal = R_Fatal+ [np.sum(i) for i in node_config.R_Fatal]
    avg_rate_frac = (node_config.param[-1]['rate_frac'][0])*2.3
    calc = {'I':I[:200], 'R': R[:200], 'hospitalized':Severe_H[:200], 'fatal':R_Fatal[:200], 'Rt':avg_rate_frac}
    return calc

def slope_calc(a):
    i,slope=0,[]
    while i < len(a)-2:
        slope.append((a[i+2]-a[i])/2)
        i+=1
    return np.array(slope)

def rms_cal(ts, value,nodal_config,key,t,match_period):
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
    I_cal = ts[ts["Date Announced"] <= FIRSTJAN+ datetime.timedelta(days=t-1)]
    I_real=list(I_cal[-match_period:]['cumsum']) if key!='rate_frac' else slope_calc(list(I_cal[-match_period:]['cumsum']))
    I_dist=(I_pred/I_mult)-(np.array(I_real))
    rms_dist=np.sqrt(np.mean(I_dist*I_dist))
    return rms_dist


def optimize_param(ts, node1_local_config,key,today,p_range=[0,100],match_period=7):
    min_val=p_range[0]
    max_val=p_range[1]
    thresh=0.05 if key=="rate_frac" else 4
    while True:
        mid_val=(min_val+max_val)/2 if key=="rate_frac" else int((min_val+max_val)/2)
        if abs(min_val-max_val)<thresh:
            if rms_cal(ts, mid_val,node1_local_config,key,today,match_period)>rms_cal(ts, min_val,node1_local_config,key,today,match_period):
                return min_val
            elif rms_cal(ts, mid_val,node1_local_config,key,today,match_period)>rms_cal(ts, max_val,node1_local_config,key,today,match_period):
                return max_val
            else:
                return mid_val
        elif rms_cal(ts, mid_val,node1_local_config,key,today,match_period)>rms_cal(ts, mid_val-thresh/2,node1_local_config,key,today,match_period):
            max_val=mid_val
        else:
            min_val=mid_val


network_epidemic_calc = MemoizeMutable(unmemoized_network_epidemic_calc)

def json_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
    if isinstance(o, np.ndarray):
        return np.round(o, 2).tolist()
    if isinstance(o, np.int64):
        return int(o)

def run_epidemic_calc_district():
    district_stats = []
    for dist in district_node_config:
        # if dist['node'] in ['new delhi', 'nashik']:
        dist_data = district_series[district_series.District == dist['node']].reset_index()
        cumsum = dist_data['cumsum'].tolist()
        dist_stats = network_epidemic_calc(dist_data, dist)
        dist_stats.update({'State':dist_data['State'][0], 'District':dist['node'],
        'Date Announced':dist_data['Date Announced'].tolist(), 'cumsum':cumsum})
        district_stats.append(dist_stats)
    with open('data/district_stats.json', 'w') as fout:
        json.dump(district_stats , fout, default=json_converter)

def run_epidemic_calc_state(days):
    stats = []
    country_I, country_R, country_H, country_fatal = \
        np.array([0] * days), np.array([0] * days), np.array([0] * days), np.array([0] * days)
    aggregated = states_series.groupby("Date Announced",as_index=False)["cumsum"].sum().reset_index()
    for state in node_config_list:
        state_data = states_series[states_series.States == state['node']].reset_index()
        cumsum = state_data['cumsum'].tolist()
        state_stats = network_epidemic_calc(state_data, state)
        state_stats.update({'State':state['node'], 
                            'Date Announced':state_data['Date Announced'].tolist(),
                            'cumsum':cumsum})
        stats.append(state_stats)
        country_I += state_stats['I'].astype(int)
        country_R += state_stats['R'].astype(int)
        country_H += state_stats['hospitalized'].astype(int)
        country_fatal += state_stats['fatal'].astype(int)

    rate_frac_list = [x['Rt'] for x in stats]
    avg_rate_frac = np.mean(rate_frac_list)
    country_stats = {'I':country_I, 'R':country_R, 'hospitalized':country_H, 'fatal':country_fatal,
                     'Rt':avg_rate_frac, 'State':'India', 'cumsum':aggregated['cumsum'].tolist(),
                     'Date Announced':aggregated['Date Announced'].tolist()}
    stats.append(country_stats)
    with open('data/state_stats.json', 'w') as fout:
        json.dump(stats , fout, default=json_converter)

# run_epidemic_calc_district()
# run_epidemic_calc_state(days=200)
