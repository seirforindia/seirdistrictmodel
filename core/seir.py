import random
import plotly.graph_objects as go
import numpy as np
from operator import itemgetter
import json
from datetime import datetime, timedelta
import copy
import _pickle as cPickle
import pandas as pd
from configuration import *
from file_locator import *
from scrap import *


import csv
import os
import matplotlib.pyplot as plt

CFR_div=1
I_mult=1
rate_range=[0,0.76]
# rate_range=[0,1]

class MemoizeMutable:
    def __init__(self, fn):
        self.fn = fn
        self.memo = {}
    def __call__(self, *args, **kwds):
        str = cPickle.dumps(args, 1)+cPickle.dumps(kwds, 1)
        if not str in self.memo:
            self.memo[str] = self.fn(*args, **kwds)
        return self.memo[str]

def add_optimize_param_to_config(ts, local_config, node_config, tn, I_range):
    intial_jump,jump,delay=5,5,5
    ts["Date Announced"] = pd.to_datetime(ts["Date Announced"])
    latest_day=int((ts['Date Announced'][len(ts)-1]-FIRSTJAN).days)+1
    new_param=[]
    node_config.param=new_param
    for d in range(intial_jump+tn,latest_day-jump+1,jump):
        period=jump if d+jump*2<=latest_day else latest_day-d
        ratefrac=optimize_param(ts, node_config,"rate_frac",d+period,rate_range,period)
        rate_frac_opt=np.array([ratefrac]*4)
        new_param.append({"intervention_day":d-delay,"rate_frac":rate_frac_opt})
        node_config.param=new_param
        I_opt=optimize_param(ts, node_config,"I0",d+period,I_range,period)
        if abs(I_opt-np.sum(node_config.I0))>2:
            node_config.I0=np.round(I_opt*node_config.pop_frac)
            node_config.E0=np.round(1.5*I_opt*node_config.pop_frac)

    node_config = SeirConfig(nodal_config=local_config,global_config=global_dict)
    try:
        node_config.I0=np.round(I_opt*node_config.pop_frac)
        node_config.E0=np.round(1.5*node_config.I0)
        node_config.param=new_param
        # print("Changable Parameters list on intervention for this node :  ",node_config.param)
    except:
        node_config.I0=np.round(50*node_config.pop_frac)
        node_config.E0=np.round(1.5*node_config.I0)
    return node_config

def unmemoized_network_epidemic_calc(data, local_config, days=200, I_range=[0,2500]):
    cumsum = data['cumsum'].tolist()
    lat_death_c = data['deathCount'].tolist()[-1]
    # print(I_range)
    I, R, Severe_H, R_Fatal = np.array([0] * days), np.array([0] * days), np.array([0] * days), np.array([0] * days)
    node_config = SeirConfig(nodal_config=local_config,global_config=global_dict)
    tn = node_config.t0
    node_config = add_optimize_param_to_config(data, local_config, node_config, tn, I_range)

    node_config.getSolution(days)
    I = I + [np.sum(i) for i in node_config.I]
    R = R+ [np.sum(i) for i in node_config.R]
    Severe_H = Severe_H+ [np.sum(i) for i in node_config.Severe_H]
    R_Fatal = R_Fatal+ [np.sum(i) for i in node_config.R_Fatal]
    try:
        avg_rate_frac = np.round((node_config.param[-1]['rate_frac'][0])*2.3, 2)
    except:
        avg_rate_frac = 0
    motarity_rate = lat_death_c / cumsum[-16]
    fatal = motarity_rate*(I+R)
    calc = {'cumsum': cumsum, 'I':I, 'R': R, 'hospitalized':Severe_H, 
            'fatal':fatal, 'Rt':avg_rate_frac, 'Mt':round(motarity_rate*100, 2)}
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
    I_cal = ts[ts["Date Announced"] <= FIRSTJAN+ timedelta(days=t-1)]
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
    if isinstance(o, datetime):
        return o.__str__()
    if isinstance(o, np.ndarray):
        return np.round(o, 2).tolist()
    if isinstance(o, np.int64):
        return int(o)

def run_epidemic_calc_district():
    district_stats = []
    state_dist = district[['State','District']].drop_duplicates()
    for dist in state_dist.itertuples():
        dist_data = district_series[(district_series.District == dist.District)\
             & (district_series.State == dist.State)].reset_index()
        print('State: {}, District: {}'.format(dist.State, dist.District))
        # ignore very less data points
        if dist_data.shape[0]<3:
            continue
        node = list(filter(lambda n: n["node"] == dist.District and n["State"]\
             == dist.State, district_node_config))[0]
        try:
            dist_stats = network_epidemic_calc(dist_data, node)
        except:
            continue
        dist_stats.update({'State':dist.State, 'District':dist.District,
                           'Date Announced':dist_data['Date Announced'].tolist()})
        district_stats.append(dist_stats)

    district_stats_filename = f"{DATA_DIR}/{DISTRICT_STATS}"
    with open(district_stats_filename, 'w') as fout:
        json.dump(district_stats , fout, default=json_converter)

    upload_to_aws(district_stats_filename, OPTIMIZER_BUCKET_NAME,
        f"{BUCKET_DIR}/{DISTRICT_STATS}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    return

def run_epidemic_calc_state(days):
    stats = []
    for state in node_config_list:
        print('State: {}'.format(state['node']))
        state_data = states_series[states_series.States == state['node']].reset_index()
        state_stats = network_epidemic_calc(state_data, state, days)
        state_stats.update({'State':state['node'],
                            'Date Announced':state_data['Date Announced'].tolist(),
                            'test_per': cal_pos(state['node'])})
        stats.append(state_stats)
    country_data = states_series.groupby(['Date Announced']).sum().reset_index()
    country_data_stats = network_epidemic_calc(country_data, India_node, days, I_range=[0, 30000])
    country_data_stats.update({'State':'India',
                        'Date Announced':country_data['Date Announced'].tolist(),
                        'test_per': cal_pos('India')})
    stats.append(country_data_stats)
    state_stats_filename = f"{DATA_DIR}/{STATE_STATS}"
    with open(state_stats_filename, 'w') as fout:
        json.dump(stats , fout, default=json_converter)

    upload_to_aws(state_stats_filename, OPTIMIZER_BUCKET_NAME,
        f"{BUCKET_DIR}/{STATE_STATS}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    return stats


def create_flourish_data():

    state_wise_total_infection_filename = f"{DATA_DIR}/{STATE_WISE_TOTAL_INFECTION}"
    district_wise_total_infection_filename = f"{DATA_DIR}/{DISTRICT_WISE_TOTAL_INFECTION}"
    top_5_test_positive_filename = f"{DATA_DIR}/{TOP_5_TEST_POSTIVE}"
    top_5_mortality_filename = f"{DATA_DIR}/{TOP_5_MORTALITY}"
    test_postive_timeseries_filename = f"{DATA_DIR}/{TEST_POSITIVE_TIMESERIES}"
    mortality_timeseries_filename = f"{DATA_DIR}/{MORTALITY_TIMESERIES}"

    testing=pd.read_csv("https://api.covid19india.org/csv/latest/statewise_tested_numbers_data.csv")
    states_data=pd.read_csv("https://api.covid19india.org/csv/latest/state_wise_daily.csv")
    deceased=states_data[states_data['Status'].str.contains('Deceased')].cumsum()
    confirmed=states_data[states_data['Status'].str.contains('Confirmed')].cumsum()
    state_code_link=pd.read_csv("https://api.covid19india.org/csv/latest/state_wise.csv")

    state_code_link[1:][['State','Confirmed','Recovered',   'Deaths',   'Active',   'Last_Updated_Time' ]].to_csv(state_wise_total_infection_filename,index=False)
    disctrict_data=pd.read_csv("https://api.covid19india.org/csv/latest/district_wise.csv")
    disctrict_data[1:][['State','District','Confirmed','Recovered', 'Deceased', 'Active'    ]].to_csv(district_wise_total_infection_filename,index=False)

    if os.path.exists(top_5_test_positive_filename):
        os.remove(top_5_test_positive_filename)
    if os.path.exists(top_5_mortality_filename):
        os.remove(top_5_mortality_filename)

    state_grp=testing.groupby('State')
    aligned_data = []
    line=0
    for name,grp in state_grp:
        if len(grp)>=45:
            state_code=str(state_code_link[state_code_link['State']==name]['State_code']).split('\n')[0][-2:]
            state=grp[['Updated On']]
            state['Total Tested']=grp['Total Tested'].diff()
            state['Positive']=grp['Positive'].diff()
            state['Total Infected']=grp['Positive']
            if int(state['Positive'].sum())>500:
                state=state[-45:]
                state['Infected_20D']=list(confirmed[state_code][-60:-15])
                state['Deaths']=list(deceased[state_code][-45:])
                # print('State Name: ',state_name)
                state_name=name
                state.dropna()
                test_pos=[]
                mortality=[]
                date=[]
                state['Mortality']=state['Deaths']/state['Infected_20D']*100
                for index in range(len(state)-4):
                    df=state[index:index+5]
                    if int(df['Total Tested'].sum())>0 and int(df['Infected_20D'].sum())>0 and int(df['Deaths'].sum())>=0:
                        test_pos.append(round((int(df['Positive'].sum())/int(df['Total Tested'].sum())*100),2))
                        date.append(str(df[4:5]['Updated On']).split('\n')[0][-10:])
                        mortality.append(round(list(state['Mortality'])[index+4],2))
                    else:
                        date.append(str(df[4:5]['Updated On']).split('\n')[0][-10:])
                        df=state[index-5:index]
                        test_pos.append(round((int(df['Positive'].sum())/int(df['Total Tested'].sum())*100),2))
                        mortality.append(round(list(state['Mortality'])[index+4],2))

                with open(top_5_test_positive_filename, 'a') as csvfile: 
                    csvwriter = csv.writer(csvfile)
                    if line==0:
                        csvwriter.writerow(['state']+date) 
                    csvwriter.writerow([str(state_name)]+test_pos) 

                with open(top_5_mortality_filename, 'a') as csvfile: 
                    csvwriter = csv.writer(csvfile)
                    if line==0:
                        csvwriter.writerow(['state']+date) 
                    csvwriter.writerow([str(state_name)]+mortality) 
                line+=1
                aligned_data.append(pd.DataFrame({'State':state_name,'Date':date,'Test Positivity Rate':test_pos, 'Mortality Rate':mortality}))
    abc=pd.concat(aligned_data)
    abc[['State','Date','Test Positivity Rate']].to_csv(test_postive_timeseries_filename,index=False)
    abc[['State','Date','Mortality Rate']].to_csv(mortality_timeseries_filename,index=False)


    testpos=pd.read_csv(top_5_test_positive_filename)
    testpos=testpos[testpos['state'].str.contains('Maharashtra|Delhi|Tamil Nadu|Gujarat|Uttar Pradesh')].transpose()
    testpos.to_csv(top_5_test_positive_filename)
    with open(top_5_test_positive_filename, 'r') as fin:
        data = fin.read().splitlines(True)
    with open(top_5_test_positive_filename, 'w') as fout:
        fout.writelines(data[1:])

    mortality=pd.read_csv(top_5_mortality_filename)
    mortality=mortality[mortality['state'].str.contains('Maharashtra|Delhi|Tamil Nadu|Gujarat|Uttar Pradesh')].transpose()
    mortality.to_csv(top_5_mortality_filename)
    with open(top_5_mortality_filename, 'r') as fin:
        data = fin.read().splitlines(True)
    with open(top_5_mortality_filename, 'w') as fout:
        fout.writelines(data[1:])
    print("s3 Upload started for flourish data")
    upload_to_aws(state_wise_total_infection_filename, OPTIMIZER_BUCKET_NAME,
        f"{FLOURISH_BUCKET_DIR}/{STATE_WISE_TOTAL_INFECTION}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    upload_to_aws(district_wise_total_infection_filename, OPTIMIZER_BUCKET_NAME,
        f"{FLOURISH_BUCKET_DIR}/{DISTRICT_WISE_TOTAL_INFECTION}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    upload_to_aws(top_5_test_positive_filename, OPTIMIZER_BUCKET_NAME,
        f"{FLOURISH_BUCKET_DIR}/{TOP_5_TEST_POSTIVE}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    upload_to_aws(top_5_mortality_filename, OPTIMIZER_BUCKET_NAME,
        f"{FLOURISH_BUCKET_DIR}/{TOP_5_MORTALITY}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    upload_to_aws(test_postive_timeseries_filename, OPTIMIZER_BUCKET_NAME,
        f"{FLOURISH_BUCKET_DIR}/{TEST_POSITIVE_TIMESERIES}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    upload_to_aws(mortality_timeseries_filename, OPTIMIZER_BUCKET_NAME,
        f"{FLOURISH_BUCKET_DIR}/{MORTALITY_TIMESERIES}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
    return

state_stats = run_epidemic_calc_state(250)
run_epidemic_calc_district()
prepare_state_map_data(state_stats)
prepare_state_wise_Rt(state_stats)
prepare_age_wise_estimation(state_stats,250)
create_flourish_data()
