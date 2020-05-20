import csv
from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import numpy as np
import pathlib
import os
import datetime
import json
import boto3
from botocore.exceptions import NoCredentialsError

optimize_param_flag = True
FIRSTJAN = datetime.datetime(2020,1,1,0,0,0,0)

ACCESS_KEY = 'AKIAIORXV5HQEGT2JXUQ'
SECRET_KEY = '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'


def modify_optimize_param_flag(flag):
    global optimize_param_flag
    optimize_param_flag = flag

district_node_config=[]
def get_district_nodal_config():
    global district_node_config
    node_data = district[['District', 'Population', 'TN']]
    node_data.columns = ['node','pop','t0']
    district_node_config = node_data.to_dict('Records')

node_config_list=[]
def get_nodal_config(nodes):
    global node_config_list
    node_config_list=[]
    for node in nodes:
        if node["node"] in states.States.to_list():
            state_default_params = states.loc[states.States==node["node"],["States","Population","TN"]]. \
                rename(columns ={"States":"node","Population":"pop","TN":"t0"}).to_dict('r')[0]
            state_default_params.update(node)
            if "nodal_param_change" in state_default_params.keys():
                for param in state_default_params["nodal_param_change"]:
                    param["intervention_day"] = (datetime.datetime.strptime(param["intervention_date"],'%m-%d-%Y') - FIRSTJAN).days
            node_config_list.append(state_default_params)

global_dict={}
def get_global_dict(my_dict):
    global global_dict
    for intervention in my_dict["param"]:
        intervention["intervention_type"] = "global"
        intervention["intervention_day"] = (datetime.datetime.strptime(intervention["intervention_date"],'%m-%d-%Y') - FIRSTJAN).days
    global_dict=my_dict

with open('data/global.json') as g :
    raw_dict = json.load(g)
    get_global_dict(raw_dict)

# url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSc_2y5N0I67wDU38DjDh35IZSIS30rQf7_NYZhtYYGU1jJYT6_kDx4YpF-qw0LSlGsBYP8pqM_a1Pd/pubhtml#"

def properties(x):
    grads = list(x.sort_values(by="Date Announced", ascending=True)["numcases"].diff(periods=1).fillna(0))
    if len(grads) > 1:
        delta = int(grads[-2])
    else:
        delta = int(grads[-1])
    sigma = int(x["numcases"].sum())
    today = int(list(x.sort_values(by="Date Announced", ascending=True)["numcases"].fillna(0))[-1])
    frame = list(x.sort_values(by="Date Announced", ascending=True)["Date Announced"].fillna(0))
    first_report = frame[0]
    return pd.Series({"Reported": first_report, "Sigma": sigma, "Delta": delta, "Today": today,
                      "Day": int((frame[-1] - frame[0]).days)})

def squash(x):
    i = x.min()
    a = x.max()
    return ((x - i) / (a - i)) + 0.7


def t_n(x,n=50):

    x = x.sort_values(by="Date Announced", ascending=True)
    x.reset_index()
    x['numcases'] = x['numcases'].cumsum()
    # fnd the day when patient.cumsum() crosses n and return that day number repsect to 1 jan
    # for other states don't show in screen
    if list(x['numcases'])[-1]<n:
        return -1
    day_crossed = list(x[x['numcases']>=n]['Date Announced'])
    return ((day_crossed[0] - FIRSTJAN).days + 1)

def unpivot(frame):
    N, K = frame.shape
    data = {'numcases': frame.to_numpy().ravel('F'),
            'state_code': np.asarray(frame.columns).repeat(N),
            'date': np.tile(np.asarray(frame.index), K)}
    return pd.DataFrame(data, columns=['date', 'state_code', 'numcases'])

states = pd.read_csv("data/States.csv")
statesCode = pd.read_csv('data/statesCode.csv')


# dataSource=pd.read_csv('core/state_wise_daily.csv')
dataSource=pd.read_csv('https://api.covid19india.org/csv/latest/state_wise_daily.csv')
confirmedMatrix=dataSource[dataSource['Status'].str.contains('Confirmed')]
confirmedMatrix.set_index('Date', inplace=True)
confirmedMatrix.drop(['Status', 'TT'], axis=1, inplace=True)
# print(confirmedMatrix.columns)
df = unpivot(confirmedMatrix)
df['numcases'] = df['numcases'].fillna(0)
df = df.astype({'numcases':'int'})
# print(df.columns)

# correcting State code in input
df.state_code = df.state_code.replace('CT', 'CG')
df.state_code = df.state_code.replace('UT', 'UK')
df.state_code = df.state_code.replace('TG', 'TS')
df = df.merge(statesCode, how='left', left_on="state_code", right_on="Statecode")
df['Date Announced'] = pd.to_datetime(df["date"], format='%d-%b-%y')
# print(df.head())
t_n_data = df.groupby("States").apply(t_n,(global_dict["I0"])).reset_index().rename({0:"TN"},axis=1)
states_series = df.groupby(["States", "Latitude", "Longitude", "Date Announced"], as_index=False)[
    "numcases"].sum()
# print(states_series.tail())
states = states_series.groupby(["States", "Latitude", "Longitude"], as_index=False).apply(properties).reset_index()
population = pd.read_csv("data/population.csv", usecols=["States", "Population"])
states = states.merge(population, on="States")
states["TNaught"] = (states.Reported - FIRSTJAN).dt.days
states["Population"] = states["Population"].astype(int)
states = states.merge(t_n_data, on="States")
states = states[states.TN>0]
states['perDelta'] = round(states['Delta']*100/states['Sigma'], 2)
states[states.TN>0].to_csv("data/covid.csv", index=False)
states_series.to_csv("data/covid_Series.csv", index=False)

districts_daily_data = pd.read_json("data/districts_daily.json", orient='Records')
# districts_daily_data = pd.read_json("https://api.covid19india.org/districts_daily.json", orient='Records')
# data is in format {"districtsDaily": {"State": {"District": [{
#  "active": 0,"deceased": 0, "recovered": 1, "date": "2020-04-21"}]}}

districts_daily_data = districts_daily_data['districtsDaily']
dist_data = []
cols = ['State','District', 'cumsum','numcases', 'date']
for state,state_data in districts_daily_data.items():
  for district,district_data in state_data.items():
    count = 0
    for daily in district_data:
        if count == 0:
            dist_data.append((state, district,daily['confirmed'], daily['confirmed'], daily['date']))
        else:
            previous_confirmed = dist_data[-1][-3]
            dist_data.append((state, district, daily['confirmed'], daily['confirmed']-previous_confirmed, daily['date']))
        count += 1

dist_data = pd.DataFrame(dist_data)
print(dist_data.head())
dist_data.columns = cols

district_pop = pd.read_csv('data/districts-population.csv')

# clean up for district name variation
district_names = district_pop.knownNames.str.strip()
dist_var_names = district_names[district_names.str.find(',')>0]
for i in dist_var_names:
    keys = i.split(',')
    dist_data['District'][dist_data['District'].isin(keys[1:])] = keys[0]
district_pop = district_pop[['Name', 'Population']]
district_pop.Population = district_pop.Population.astype(int)
district_pop.Name = district_pop.Name.str.strip()
district_pop.Name = district_pop.Name.str.lower()
dist_data.District = dist_data.District.str.strip()
dist_data.District = dist_data.District.str.lower()

dist_data['Date Announced'] = pd.to_datetime(dist_data["date"], format='%Y-%m-%d')

district_series = dist_data.groupby(["State", "District", "Date Announced"], as_index=False)[
    "numcases"].sum()
district = district_series.groupby(["District"]).apply(properties).reset_index()
district = district.merge(district_pop, left_on="District", right_on="Name")
district["TNaught"] = (district.Reported - FIRSTJAN).dt.days
t_n_data = dist_data.groupby("District").apply(t_n,(global_dict["I0"])).reset_index().rename({0:"TN"},axis=1)
district = district.merge(t_n_data, on="District")
district = district[district.TN>0]
district['perDelta'] = round(district['Delta']*100/district['Sigma'], 2)
# district[district.TN>0].to_csv("data/covid_district.csv", index=False)
# district_series.to_csv("data/covid_district_Series.csv", index=False)

get_district_nodal_config()

with open('data/nodal.json') as f:
    raw_nodes = json.load(f)
    get_nodal_config(raw_nodes)

def prepare_state_wise_Rt(state_wise_data):
    df = pd.DataFrame(state_wise_data)
    df = df.drop('I+R', axis=1)
    df.Rt = round(df.Rt, 2)
    df.to_csv('data/state_wise_Rt.csv', index=False)
    upload_to_aws('data/state_wise_Rt.csv','covid19-seir-plus','state_wise_Rt')

def prepare_age_wise_estimation(T, state_wise_data):
    prepare_state_wise_Rt(state_wise_data)
    pop_frac = global_dict["pop_frac"]
    print(pop_frac)
    # print(type(pop_frac))
    mid_may = datetime.date(2020, 5, 15)
    all_dates = [i.date() for i in T]
    mid_may_ind = all_dates.index(mid_may)+1
    duration = 15
    age_wise_esimation = []
    for state_data in state_wise_data:
        for i in range(mid_may_ind, len(all_dates), duration):
            curr_est = {}
            curr_est['Date'] = all_dates[i].strftime("%d-%b-%y")
            curr_est['state'] = state_data['state']
            curr_est['total Infected'] = (state_data['I+R'][i])
            curr_est['Age 0-19'] = round(state_data['I+R'][i]*pop_frac[0])
            curr_est['Age 20-39'] = round(state_data['I+R'][i]*pop_frac[1])
            curr_est['Age 40-59'] = round(state_data['I+R'][i]*pop_frac[2])
            curr_est['Age 60+'] = round(state_data['I+R'][i]*pop_frac[3])
            age_wise_esimation.append(curr_est)
    df = pd.DataFrame(age_wise_esimation)
    df = df.astype({'total Infected':'int','Age 0-19':'int', 'Age 20-39':'int','Age 40-59':'int','Age 60+':'int'})
    df.to_csv('data/age_wise_estimation.csv', index=False)
    upload_to_aws('data/age_wise_estimation.csv','covid19-seir-plus','age_wise_estimation')




def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)
    try:
        dateTimeObj = datetime.datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
        s3.upload_file(local_file, bucket, s3_file + timestampStr + '.csv' )
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

with open("data/district_stats.json") as district_robj, open("data/state_stats.json") as state_robj:
    district_stats_list = json.loads(district_robj.read())
    state_stats_list = json.loads(state_robj.read())
