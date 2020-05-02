import csv
from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import pathlib
import os
import datetime
import json

optimize_param_flag = False

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
                    param["intervention_day"] = (datetime.datetime.strptime(param["intervention_date"],'%m-%d-%Y') - datetime.datetime(2020,1,1,0,0,0,0)).days
            node_config_list.append(state_default_params)

global_dict={}
def get_global_dict(my_dict):
    global global_dict
    for intervention in my_dict["param"]:
        intervention["intervention_type"] = "global"
        intervention["intervention_day"] = (datetime.datetime.strptime(intervention["intervention_date"],'%m-%d-%Y') - datetime.datetime(2020,1,1,0,0,0,0)).days
    global_dict=my_dict

with open('data/global.json') as g :
    raw_dict = json.load(g)
    get_global_dict(raw_dict)

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSc_2y5N0I67wDU38DjDh35IZSIS30rQf7_NYZhtYYGU1jJYT6_kDx4YpF-qw0LSlGsBYP8pqM_a1Pd/pubhtml#"

def properties(x):
    grads = list(x.sort_values(by="Date Announced", ascending=True)["Patient Number"].diff(periods=1).fillna(0))
    if len(grads) > 1:
        delta = int(grads[-2])
    else:
        delta = int(grads[-1])
    sigma = int(x["Patient Number"].sum())
    today = int(list(x.sort_values(by="Date Announced", ascending=True)["Patient Number"].fillna(0))[-1])
    frame = list(x.sort_values(by="Date Announced", ascending=True)["Date Announced"].fillna(0))
    first_report = frame[0]
    return pd.Series({"Reported": first_report, "Sigma": sigma, "Delta": delta, "Today": today,
                      "Day": int((frame[-1] - frame[0]).days)})

def squash(x):
    i = x.min()
    a = x.max()
    return ((x - i) / (a - i)) + 0.7

def t_n(x,n=50):
    _arr = list(x.sort_values(by="Date Announced", ascending=True)["Date Announced"])
    if len(_arr)>n:
        return (list(x.sort_values(by="Date Announced", ascending=True)["Date Announced"])[n] - datetime.datetime(2020,1,1,0,0,0,0)).days
    else :return len(_arr) -n

states = pd.read_csv("data/States.csv")
df =pd.read_json("https://api.covid19india.org/raw_data.json",orient = 'records')
df = pd.read_json(df["raw_data"].to_json(),orient='index')
df.rename(columns={"dateannounced":"Date Announced","detectedstate":"Detected State","patientnumber":"Patient Number"},inplace=True)
df = df[(df["Date Announced"].notnull()) & (df["Date Announced"] != "")]
df["Date Announced"] = pd.to_datetime(df["Date Announced"], format='%d/%m/%Y')
df = df.merge(states, how='left', left_on="Detected State", right_on="States")
t_n_data = df.groupby("States").apply(t_n,(global_dict["I0"])).reset_index().rename({0:"TN"},axis=1)
states_series = df.groupby(["States", "Latitude", "Longitude", "Date Announced"], as_index=False)[
    "Patient Number"].count()
states = states_series.groupby(["States", "Latitude", "Longitude"], as_index=False).apply(properties).reset_index()
population = pd.read_csv("data/population.csv", usecols=["States", "Population"])
states = states.merge(population, on="States")
states["TNaught"] = (states.Reported - datetime.datetime(2020,1,1,0,0,0,0)).dt.days
states["Population"] = states["Population"].astype(int)
states = states.merge(t_n_data, on="States")
states = states[states.TN>0]
# states[states.TN>0].to_csv("data/covid.csv", index=False)
# states_series.to_csv("data/covid_Series.csv", index=False)

with open('data/nodal.json') as f:
    raw_nodes = json.load(f)
    get_nodal_config(raw_nodes)


