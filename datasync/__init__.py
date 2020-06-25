import os

ACCESS_KEY = os.environ['ACCESS_KEY']
SECRET_KEY = os.environ['SECRET_KEY']

OPTIMIZER_ACCESS_KEY=os.environ['OPTIMIZER_ACCESS_KEY']
OPTIMIZER_SECRET_KEY=os.environ['OPTIMIZER_SECRET_KEY']

OPTIMIZER_BUCKET_NAME=os.environ['OPTIMIZER_ACCESS_KEY']

DISTRICT_STATS = 'district_stats.json'
STATE_STATS = 'state_stats.json'
MAP_STATE = 'state_map_data.csv'
DATA_DIR = 'data'
BUCKET_DIR = 'optimizer_data'
FLOURISH_BUCKET_DIR = 'flourish_data'

#flourishfiles
STATE_WISE_TOTAL_INFECTION = 'state_wise_total_infection.csv'
DISTRICT_WISE_TOTAL_INFECTION = 'district_wise_total_infection.csv'
TOP_5_TEST_POSTIVE = 'top_5_test_positive.csv'
TOP_5_MORTALITY = 'top_5_mortality.csv'
TEST_POSITIVE_TIMESERIES = 'test_postive_timeseries.csv'
MORTALITY_TIMESERIES = 'mortality_timeseries.csv'
