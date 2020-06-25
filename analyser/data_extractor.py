from datasync.file_locator import *
import pandas as pd
from datetime import timedelta, date
import numpy as np
from analyser import *

class Extractor:

    district_daily = "https://api.covid19india.org/districts_daily.json"

    @classmethod
    def prepare_districts(cls):
        districts_daily_data = pd.read_json(cls.district_daily, orient='Records')
        districts_daily_data = districts_daily_data['districtsDaily']
        dist_data = []
        cols = ['State', 'District', 'cumsum', 'deathCount', 'date']
        for state,state_data in districts_daily_data.items():
            for district,district_data in state_data.items():
                count = 0
                for daily in district_data:
                    dist_data.append((state, district,daily['confirmed'],daily['deceased'], daily['date']))

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
        start_date = dist_data['Date Announced'].min()
        district_series = dist_data.groupby(["State", "District", "Date Announced"], as_index=False)[
            ["cumsum", "deathCount"]].sum()
        district = district_series.groupby(['State', "District"]).apply(properties).reset_index()

        district = district.merge(district_pop, left_on="District", right_on="Name", how='left')
        district.Population = district.Population.fillna(2000000)

        district["TNaught"] = (district.Reported - FIRSTJAN).dt.days
        t_n_data = dist_data.groupby(['State', "District"]).apply(t_n,20).reset_index().rename({0:"TN"},axis=1)
        district = district.merge(t_n_data, on=["District","State"])
        district = district[district.TN>0]
        district['perDelta'] = round(district['Delta']*100/district['Sigma'], 2)
        district[district.TN>0].to_csv("data/covid_district.csv", index=False)
        district_series.to_csv("data/covid_district_Series.csv", index=False)

        return district,district_series

    @classmethod
    def prepare_states(cls, district_series, global_dict):
        states = pd.read_csv("data/States.csv")
        state_series_data = district_series.drop('District', axis=1)
        state_series = state_series_data.groupby(['State', 'Date Announced']).sum().reset_index()
        df = state_series.merge(states, left_on='State', right_on='States')
        t_n_data = df.groupby("States").apply(t_n,(global_dict["I0"])).reset_index().rename({0:"TN"},axis=1)
        states_series = df.groupby(["States", "Latitude", "Longitude", "Date Announced"], as_index=False)[
            ["cumsum", "deathCount"]].max()
        states = states_series.groupby(["States", "Latitude", "Longitude"], as_index=False).apply(properties).reset_index()
        population = pd.read_csv("data/population.csv", usecols=["States", "Population"])
        states = states.merge(population, on="States")
        states["TNaught"] = (states.Reported - FIRSTJAN).dt.days
        states["Population"] = states["Population"].astype(int)
        states = states.merge(t_n_data, on="States")
        states = states[states.TN>0]
        states['perDelta'] = round(states['Delta']*100/states['Sigma'], 2)
        states_series.to_csv(f"data/covid_series.csv", index=False)
        return states, states_series

    @classmethod
    def prepare_state_map_data(cls,state_wise_data, states):
        state_rt_data = [{'States':i['State'], 'Rt':i['Rt']} for i in state_wise_data]
        df = pd.DataFrame(state_rt_data)
        state_map_data = states.merge(df, on='States')
        state_map_data.to_csv(f"{DATA_DIR}/{MAP_STATE}", index=False)
        FileLoader.upload_to_aws(f"{DATA_DIR}/{MAP_STATE}",OPTIMIZER_BUCKET_NAME,
                                 f"{BUCKET_DIR}/{MAP_STATE}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)

    @classmethod
    def prepare_state_wise_Rt(cls, state_wise_data):
        state_rt_data = [{'State':i['State'], 'Rt':i['Rt']} for i in state_wise_data]
        df = pd.DataFrame(state_rt_data)
        df.to_csv('data/state_wise_Rt.csv', index=False)
        s3_filename = f"state_wise_Rt{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}.csv"
        FileLoader.upload_to_aws('data/state_wise_Rt.csv','covid19-seir-plus', s3_filename)

    @classmethod
    def prepare_age_wise_estimation(cls, state_wise_data, days, global_dict):
        pop_frac = global_dict["pop_frac"]
        print(pop_frac)
        first_june = date(2020, 6, 1)
        T = np.array([(FIRSTJAN + timedelta(days=i)) for i in range(days)])
        all_dates = [i.date() for i in T]
        fir_jun_ind = all_dates.index(first_june)+1
        duration = 15
        age_wise_esimation = []
        for state_data in state_wise_data:
            for i in range(fir_jun_ind, len(all_dates), duration):
                curr_est = {}
                curr_est['Date'] = all_dates[i].strftime("%d-%b-%y")
                curr_est['state'] = state_data['State']
                total_infected = np.round(state_data['I'][i]+state_data['R'][i], 2)
                curr_est['total Infected'] = (total_infected)
                curr_est['Age 0-19'] = np.round(total_infected*pop_frac[0])
                curr_est['Age 20-39'] = np.round(total_infected*pop_frac[1])
                curr_est['Age 40-59'] = np.round(total_infected*pop_frac[2])
                curr_est['Age 60+'] = np.round(total_infected*pop_frac[3])
                age_wise_esimation.append(curr_est)
        df = pd.DataFrame(age_wise_esimation)
        df = df.astype({'total Infected':'int','Age 0-19':'int', 'Age 20-39':'int','Age 40-59':'int','Age 60+':'int'})
        df.to_csv('data/age_wise_estimation.csv', index=False)

        s3_filename = f"age_wise_estimation{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}.csv"
        FileLoader.upload_to_aws('data/age_wise_estimation.csv','covid19-seir-plus', s3_filename)



def properties(x):
        x['numcases'] = x['cumsum'].diff().fillna(x['cumsum'])
        r = pd.date_range(start=x['Date Announced'].min(), end =x['Date Announced'].max())
        x = x.set_index("Date Announced").reindex(r).fillna(0).rename_axis("Date Announced").reset_index()

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

def t_n(x,n=50):

        x = x.sort_values(by="Date Announced", ascending=True)
        x.reset_index()
        # fnd the day when patient.cumsum() crosses n and return that day number repsect to 1 jan
        # for other states don't show in screen
        if list(x['cumsum'])[-1]<n:
            return -1
        day_crossed = list(x[x['cumsum']>=n]['Date Announced'])
        return ((day_crossed[0] - FIRSTJAN).days + 1)