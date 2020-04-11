import csv
from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import pathlib
import os
import datetime

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
    if len(_arr)>50:
        return (list(x.sort_values(by="Date Announced", ascending=True)["Date Announced"])[n] - datetime.datetime(2020,1,1,0,0,0,0)).days
    else :return len(_arr) -n


if not (os.path.exists("data/covid.csv") and os.path.exists("data/covid_Series.csv")):
    with urllib.request.urlopen(url) as fp:
        mybytes = fp.read()
        mystr = mybytes.decode("utf8")

    os.chdir(pathlib.Path(__file__).parent.parent.absolute())

    with open("data/covid.csv", "w", newline='') as outfile:
        writer = csv.writer(outfile)

        tree = BeautifulSoup(mystr, "lxml")
        table_tag = tree.select("table")[0]
        tab_data = [[item.text for item in row_data.select("th,td")]
                    for row_data in table_tag.select("tr")]
        for data in tab_data:
            writer.writerow(data)

    df = pd.read_csv("data/covid.csv", skiprows=[0]).iloc[:, 1:20]
    df = df[df["Date Announced"].notnull()]
    states = pd.read_csv("data/States.csv")
    df["Date Announced"] = pd.to_datetime(df["Date Announced"], format='%d/%m/%Y')
    df = df.merge(states, how='left', left_on="Detected State", right_on="States")
    t_n_data = df.groupby("States").apply(t_n).reset_index().rename({0:"TN"},axis=1)
    states_series = df.groupby(["States", "Latitude", "Longitude", "Date Announced"], as_index=False)[
        "Patient Number"].count()
    states = states_series.groupby(["States", "Latitude", "Longitude"], as_index=False).apply(properties).reset_index()
    population = pd.read_csv("data/population.csv", usecols=["States", "Population"])
    states = states.merge(population, on="States")
    states["TNaught"] = (states.Reported - datetime.datetime(2020,1,1,0,0,0,0)).dt.days
    states["Population"] = states["Population"].astype(int)
    states = states.merge(t_n_data, on="States")
    states[states.TN>0].to_csv("data/covid.csv", index=False)
    states_series.to_csv("data/covid_Series.csv", index=False)
else:
    states = pd.read_csv("data/covid.csv")
    states_series = pd.read_csv("data/covid_Series.csv")
    states["Reported"] = pd.to_datetime(states["Reported"])
