from datasync.file_locator import FileLoader
from analyser import *
from datetime import datetime
import pandas as pd
import csv

class Flourish:
    @staticmethod
    def create_flourish_data():
        state_wise_total_infection_filename = f"{DATA_DIR}/{STATE_WISE_TOTAL_INFECTION}"
        district_wise_total_infection_filename = f"{DATA_DIR}/{DISTRICT_WISE_TOTAL_INFECTION}"
        top_5_test_positive_filename = f"{DATA_DIR}/{TOP_5_TEST_POSTIVE}"
        top_5_mortality_filename = f"{DATA_DIR}/{TOP_5_MORTALITY}"
        test_postive_timeseries_filename = f"{DATA_DIR}/{TEST_POSITIVE_TIMESERIES}"
        mortality_timeseries_filename = f"{DATA_DIR}/{MORTALITY_TIMESERIES}"

        testing = pd.read_csv("https://api.covid19india.org/csv/latest/statewise_tested_numbers_data.csv")
        states_data = pd.read_csv("https://api.covid19india.org/csv/latest/state_wise_daily.csv")
        deceased = states_data[states_data['Status'].str.contains('Deceased')].cumsum()
        confirmed = states_data[states_data['Status'].str.contains('Confirmed')].cumsum()
        state_code_link = pd.read_csv("https://api.covid19india.org/csv/latest/state_wise.csv")

        state_code_link[1:][['State', 'Confirmed', 'Recovered', 'Deaths', 'Active', 'Last_Updated_Time']].to_csv(
            state_wise_total_infection_filename, index=False)
        disctrict_data = pd.read_csv("https://api.covid19india.org/csv/latest/district_wise.csv")
        disctrict_data[1:][['State', 'District', 'Confirmed', 'Recovered', 'Deceased', 'Active']].to_csv(
            district_wise_total_infection_filename, index=False)

        if os.path.exists(top_5_test_positive_filename):
            os.remove(top_5_test_positive_filename)
        if os.path.exists(top_5_mortality_filename):
            os.remove(top_5_mortality_filename)

        state_grp = testing.groupby('State')
        aligned_data = []
        line = 0
        for name, grp in state_grp:
            if len(grp) >= 34:
                state_code = str(state_code_link[state_code_link['State'] == name]['State_code']).split('\n')[0][-2:]
                state = grp[['Updated On']]
                state['Total Tested'] = grp['Total Tested'].diff()
                state['Positive'] = grp['Positive'].diff()
                state['Total Infected'] = grp['Positive']
                if int(state['Positive'].sum()) > 500:
                    state = state[-34:]
                    state['Infected_20D'] = list(confirmed[state_code][-49:-15])
                    state['Deaths'] = list(deceased[state_code][-34:])
                    # print('State Name: ',state_name)
                    state_name = name
                    state.dropna()
                    test_pos = []
                    mortality = []
                    date = []
                    state['Mortality'] = state['Deaths'] / state['Infected_20D'] * 100
                    for index in range(len(state) - 4):
                        df = state[index:index + 5]
                        if int(df['Total Tested'].sum()) > 0 and int(df['Infected_20D'].sum()) > 0 and int(
                                df['Deaths'].sum()) >= 0:
                            test_pos.append(round((int(df['Positive'].sum()) / int(df['Total Tested'].sum()) * 100), 2))
                            date.append(str(df[4:5]['Updated On']).split('\n')[0][-10:])
                            mortality.append(round(list(state['Mortality'])[index + 4], 2))
                        else:
                            date.append(str(df[4:5]['Updated On']).split('\n')[0][-10:])
                            df = state[index - 5:index]
                            test_pos.append(round((int(df['Positive'].sum()) / int(df['Total Tested'].sum()) * 100), 2))
                            mortality.append(round(list(state['Mortality'])[index + 4], 2))

                    with open(top_5_test_positive_filename, 'a') as csvfile:
                        csvwriter = csv.writer(csvfile)
                        if line == 0:
                            csvwriter.writerow(['state'] + date)
                        csvwriter.writerow([str(state_name)] + test_pos)

                    with open(top_5_mortality_filename, 'a') as csvfile:
                        csvwriter = csv.writer(csvfile)
                        if line == 0:
                            csvwriter.writerow(['state'] + date)
                        csvwriter.writerow([str(state_name)] + mortality)
                    line += 1
                    aligned_data.append(pd.DataFrame(
                        {'State': state_name, 'Date': date, 'Test Positivity Rate': test_pos,
                         'Mortality Rate': mortality}))

        testpos = pd.read_csv(top_5_test_positive_filename)
        testpos.to_csv(test_postive_timeseries_filename, index=False)
        testpos = testpos[
            testpos['state'].str.contains('Maharashtra|Delhi|Tamil Nadu|Gujarat|Uttar Pradesh')].transpose()
        testpos.to_csv(top_5_test_positive_filename)
        with open(top_5_test_positive_filename, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(top_5_test_positive_filename, 'w') as fout:
            fout.writelines(data[1:])

        mortality = pd.read_csv(top_5_mortality_filename)
        mortality.to_csv(mortality_timeseries_filename, index=False)
        mortality = mortality[
            mortality['state'].str.contains('Maharashtra|Delhi|Tamil Nadu|Gujarat|Uttar Pradesh')].transpose()
        mortality.to_csv(top_5_mortality_filename)
        with open(top_5_mortality_filename, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(top_5_mortality_filename, 'w') as fout:
            fout.writelines(data[1:])
        print("s3 Upload started for flourish data")
        FileLoader.upload_to_aws(state_wise_total_infection_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{FLOURISH_BUCKET_DIR}/{STATE_WISE_TOTAL_INFECTION}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        FileLoader.upload_to_aws(district_wise_total_infection_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{FLOURISH_BUCKET_DIR}/{DISTRICT_WISE_TOTAL_INFECTION}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        FileLoader.upload_to_aws(top_5_test_positive_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{FLOURISH_BUCKET_DIR}/{TOP_5_TEST_POSTIVE}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        FileLoader.upload_to_aws(top_5_mortality_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{FLOURISH_BUCKET_DIR}/{TOP_5_MORTALITY}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        FileLoader.upload_to_aws(test_postive_timeseries_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{FLOURISH_BUCKET_DIR}/{TEST_POSITIVE_TIMESERIES}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        FileLoader.upload_to_aws(mortality_timeseries_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{FLOURISH_BUCKET_DIR}/{MORTALITY_TIMESERIES}{datetime.now().strftime('%d-%b-%Y (%H:%M:%S.%f)')}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        return
