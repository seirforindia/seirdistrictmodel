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

optimize_param_flag = False
FIRSTJAN = datetime.datetime(2020,1,1,0,0,0,0)

ACCESS_KEY = 'AKIAIORXV5HQEGT2JXUQ'
SECRET_KEY = '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'


def modify_optimize_param_flag(flag):
    global optimize_param_flag
    optimize_param_flag = flag

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

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSc_2y5N0I67wDU38DjDh35IZSIS30rQf7_NYZhtYYGU1jJYT6_kDx4YpF-qw0LSlGsBYP8pqM_a1Pd/pubhtml#"

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
# confirmedMatrix = confirmedMatrix.cumsum()
# print(confirmedMatrix.columns)
df = unpivot(confirmedMatrix)
df['numcases'] = df['numcases'].fillna(0)
df = df.astype({'numcases':'int'})
# print(df.columns)

# correcting State code in input
df.state_code = df.state_code.replace('CT', 'CG')
df.state_code = df.state_code.replace('UT', 'UK')
df.state_code = df.state_code.replace('TG', 'TS')

# filenames = ["https://api.covid19india.org/raw_data1.json", "https://api.covid19india.org/raw_data2.json", "https://api.covid19india.org/raw_data3.json"]
# df = pd.DataFrame()
# for f in filenames:
#     print (f)
#     temp = pd.read_json(f,orient = 'records')
#     temp = pd.read_json(temp["raw_data"].to_json(),orient='index')
#     df = df.append(temp, ignore_index = True)
    
# # df =pd.read_json("https://api.covid19india.org/raw_data.json",orient = 'records')
# # df = pd.read_json(df["raw_data"].to_json(),orient='index')
# df.rename(columns={"dateannounced":"Date Announced","detectedstate":"Detected State","patientnumber":"numcases"},inplace=True)
# df = df[(df["Date Announced"].notnull()) & (df["Date Announced"] != "")]
# df["Date Announced"] = pd.to_datetime(df["Date Announced"], format='%d/%m/%Y')
# df = df.merge(states, how='left', left_on="Detected State", right_on="States")

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
states[states.TN>0].to_csv("data/covid.csv", index=False)
states_series.to_csv("data/covid_Series.csv", index=False)

with open('data/nodal.json') as f:
    raw_nodes = json.load(f)
    get_nodal_config(raw_nodes)

def prepare_state_wise_Rt(state_wise_data):
    df = pd.DataFrame(state_wise_data)
    df = df.drop('I+R', axis=1)
    df.Rt = round(df.Rt, 2)
    df.to_csv('data/state_wise_Rt.csv', index=False)
    upload_to_aws('data/state_wise_Rt.csv','covid19-seir','state_wise_Rt')

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
    upload_to_aws('data/age_wise_estimation.csv','covid19-seir','age_wise_estimation')




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
