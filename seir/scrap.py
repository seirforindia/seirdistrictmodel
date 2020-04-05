import csv
from bs4 import BeautifulSoup
import urllib.request
import pandas as pd

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSc_2y5N0I67wDU38DjDh35IZSIS30rQf7_NYZhtYYGU1jJYT6_kDx4YpF-qw0LSlGsBYP8pqM_a1Pd/pubhtml#"

with urllib.request.urlopen(url) as fp:
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")

import pathlib
import os
os.chdir(pathlib.Path(__file__).parent.parent.absolute())

with open("data/patient.csv","w",newline='') as outfile:
    writer = csv.writer(outfile)

    tree = BeautifulSoup(mystr,"lxml")
    table_tag = tree.select("table")[0]
    tab_data = [[item.text for item in row_data.select("th,td")]
                    for row_data in table_tag.select("tr")]
    for data in tab_data:
        writer.writerow(data)


df = pd.read_csv("data/patient.csv",skiprows=[0]).iloc[:,1:20]
df = df[df["Date Announced"].notnull()]
states= pd.read_csv("data/States.csv")
df["Date Announced"] = pd.to_datetime(df["Date Announced"],format='%d/%m/%Y')
df = df.merge(states,how='left',left_on="Detected State",right_on= "States")

