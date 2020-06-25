import _pickle as cPickle
from analyser.configuration import *
from analyser import *
import pandas as pd
from datetime import timedelta
from datasync.file_locator import *
import json
import analyser.utils as utils
from analyser.data_extractor import Extractor
from analyser.nodes import Nodes
from analyser.ode_solver import ODESolver

range_range = [0, 0.76]
I_mult = 1
I_range = [0, 200]
rate_range = [0, 0.76]


class MemoizeMutable:
    def __init__(self, fn):
        self.fn = fn
        self.memo = {}

    def __call__(self, *args, **kwds):
        str = cPickle.dumps(args, 1) + cPickle.dumps(kwds, 1)
        if not str in self.memo:
            self.memo[str] = self.fn(*args, **kwds)
        return self.memo[str]


class SeirModel:

    def __init__(self):
        self.global_dict = Nodes.default_global_dict()
        self.district, self.district_series = Extractor.prepare_districts()
        self.states, self.states_series = Extractor.prepare_states(self.district_series, self.global_dict)
        self.ode_solver = ODESolver(SeirConfig(nodal_config={},global_config=self.global_dict))
        self.node_config_list =  Nodes.get_nodal_config(Nodes.default_nodal_dict(), self.states)
        self.district_node_config = Nodes.get_district_nodal_config(self.district)


    def add_optimize_param_to_config(self, ts, local_config, node_config, tn, I_range):
        intial_jump, jump, delay = 5, 5, 5
        ts["Date Announced"] = pd.to_datetime(ts["Date Announced"])
        latest_day = int((ts['Date Announced'][len(ts) - 1] - FIRSTJAN).days) + 1
        new_param = []
        node_config.param = new_param
        for d in range(intial_jump + tn, latest_day - jump + 1, jump):
            period = jump if d + jump * 2 <= latest_day else latest_day - d
            ratefrac = self.optimize_param(ts, node_config, "rate_frac", d + period, rate_range, period)
            rate_frac_opt = np.array([ratefrac] * 4)
            new_param.append({"intervention_day": d - delay, "rate_frac": rate_frac_opt})
            node_config.param = new_param
            I_opt = self.optimize_param(ts, node_config, "I0", d + period, I_range, period)
            if abs(I_opt - np.sum(node_config.I0)) > 2:
                node_config.I0 = np.round(I_opt * node_config.pop_frac)
                node_config.E0 = np.round(1.5 * I_opt * node_config.pop_frac)

        node_config = SeirConfig(nodal_config=local_config, global_config=self.global_dict)
        try:
            node_config.I0 = np.round(I_opt * node_config.pop_frac)
            node_config.E0 = np.round(1.5 * node_config.I0)
            node_config.param = new_param
        except:
            node_config.I0 = np.round(50 * node_config.pop_frac)
            node_config.E0 = np.round(1.5 * node_config.I0)
        return node_config

    def network_epidemic_calc(self, data, local_config, days, I_range=[0, 2500]):

        def unmemoized_network_epidemic_calc():
            cumsum = data['cumsum'].tolist()
            lat_death_c = data['deathCount'].tolist()[-1]
            I, R, Severe_H, R_Fatal = np.array([0] * days), np.array([0] * days), np.array([0] * days), np.array(
                [0] * days)
            node_config = SeirConfig(nodal_config=local_config, global_config=self.global_dict)

            tn = node_config.t0
            node_config = self.add_optimize_param_to_config(data, local_config, node_config, tn, I_range)

            self.ode_solver.getSolution(days)
            I = I + [np.sum(i) for i in node_config.I]
            R = R + [np.sum(i) for i in node_config.R]
            Severe_H = Severe_H + [np.sum(i) for i in node_config.Severe_H]
            R_Fatal = R_Fatal + [np.sum(i) for i in node_config.R_Fatal]
            try:
                avg_rate_frac = np.round((node_config.param[-1]['rate_frac'][0]) * 2.3, 2)
            except:
                avg_rate_frac = 0
            motarity_rate = lat_death_c / cumsum[-16]
            fatal = motarity_rate * (I + R)
            calc = {'cumsum': cumsum, 'I': I, 'R': R, 'hospitalized': Severe_H,
                    'fatal': fatal, 'Rt': avg_rate_frac, 'Mt': round(motarity_rate * 100, 2)}
            return calc

        return MemoizeMutable(unmemoized_network_epidemic_calc)()

    def slope_calc(self, a):
        i, slope = 0, []
        while i < len(a) - 2:
            slope.append((a[i + 2] - a[i]) / 2)
            i += 1
        return np.array(slope)

    def rms_cal(self, ts, value, nodal_config, key, t, match_period):
        if key == "I0":
            new_dict = {"I0": np.round(value * np.array(nodal_config.pop_frac)),
                        "E0": np.round(1.5 * value * np.array(nodal_config.pop_frac))}
        elif key == "rate_frac":
            a = nodal_config.param
            b = [{"intervention_day": t - match_period - 5, key: np.array([value] * 4)}]
            param_val = a + b
            new_dict = {"param": param_val}
        else:
            new_dict = {key: value}
        temp_con = nodal_config.clone()
        temp_con.__dict__.update(new_dict)
        self.ode_solver.upload_model_config(temp_con)
        self.ode_solver.getSolution(t)

        I = np.array([np.sum(i) for i in temp_con.I])
        R = np.array([np.sum(i) for i in temp_con.R])
        I_pred = (I + R)[t - match_period:t] if key != 'rate_frac' else self.slope_calc((I + R)[t - match_period:t])
        I_cal = ts[ts["Date Announced"] <= FIRSTJAN + timedelta(days=t - 1)]
        I_real = list(I_cal[-match_period:]['cumsum']) if key != 'rate_frac' else self.slope_calc(
            list(I_cal[-match_period:]['cumsum']))
        I_dist = (I_pred / I_mult) - (np.array(I_real))
        rms_dist = np.sqrt(np.mean(I_dist * I_dist))
        return rms_dist

    def optimize_param(self, ts, node1_local_config, key, today, p_range=[0, 100], match_period=7):
        min_val = p_range[0]
        max_val = p_range[1]
        thresh = 0.05 if key == "rate_frac" else 4
        while True:
            mid_val = (min_val + max_val) / 2 if key == "rate_frac" else int((min_val + max_val) / 2)
            if abs(min_val - max_val) < thresh:
                if self.rms_cal(ts, mid_val, node1_local_config, key, today, match_period) > self.rms_cal(ts, min_val,
                                                                                                          node1_local_config,
                                                                                                          key,
                                                                                                          today,
                                                                                                          match_period):
                    return min_val
                elif self.rms_cal(ts, mid_val, node1_local_config, key, today, match_period) > self.rms_cal(ts, max_val,
                                                                                                            node1_local_config,
                                                                                                            key, today,
                                                                                                            match_period):
                    return max_val
                else:
                    return mid_val
            elif self.rms_cal(ts, mid_val, node1_local_config, key, today, match_period) > self.rms_cal(ts,
                                                                                                        mid_val - thresh / 2,
                                                                                                        node1_local_config,
                                                                                                        key,
                                                                                                        today,
                                                                                                        match_period):
                max_val = mid_val
            else:
                min_val = mid_val

    def run_epidemic_calc_district(self, days):
        district_stats = []
        state_dist = self.district[['State', 'District']].drop_duplicates()
        for dist in state_dist.itertuples():
            dist_data = self.district_series[(self.district_series.District == dist.District) \
                                             & (self.district_series.State == dist.State)].reset_index()
            print('State: {}, District: {}'.format(dist.State, dist.District))
            # ignore very less data points
            if dist_data.shape[0] < 3:
                continue
            node = list(filter(lambda n: n["node"] == dist.District and n["State"] \
                                         == dist.State, self.district_node_config))[0]
            try:
                dist_stats = self.network_epidemic_calc(dist_data, node, days)
            except:
                continue
            dist_stats.update({'State': dist.State, 'District': dist.District,
                               'Date Announced': dist_data['Date Announced'].tolist()})
            district_stats.append(dist_stats)

        district_stats_filename = f"{DATA_DIR}/{DISTRICT_STATS}"
        with open(district_stats_filename, 'w') as fout:
            json.dump(district_stats, fout, default=utils.json_converter)

        FileLoader.upload_to_aws(district_stats_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{BUCKET_DIR}/{DISTRICT_STATS}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        return

    def run_epidemic_calc_state(self, days):
        stats = []
        for state in self.node_config_list:
            print('State: {}'.format(state['node']))
            state_data = self.states_series[self.states_series.States == state['node']].reset_index()
            state_stats = self.network_epidemic_calc(state_data, state, days)
            state_stats.update({'State': state['node'],
                                'Date Announced': state_data['Date Announced'].tolist(),
                                'test_per': self.cal_pos(state['node'])})
            stats.append(state_stats)
        country_data = self.states_series.groupby(['Date Announced']).sum().reset_index()
        country_data_stats = self.network_epidemic_calc(country_data, Extractor.India_node(), days, I_range=[0, 30000])
        country_data_stats.update({'State': 'India',
                                   'Date Announced': country_data['Date Announced'].tolist(),
                                   'test_per': self.cal_pos('India')})
        stats.append(country_data_stats)
        state_stats_filename = f"{DATA_DIR}/{STATE_STATS}"
        with open(state_stats_filename, 'w') as fout:
            json.dump(stats, fout, default=utils.json_converter)

        FileLoader.upload_to_aws(state_stats_filename, OPTIMIZER_BUCKET_NAME,
                                 f"{BUCKET_DIR}/{STATE_STATS}", OPTIMIZER_ACCESS_KEY, OPTIMIZER_SECRET_KEY)
        return stats

    def run_model(self):
        dayAfterMonth = (timedelta(35) + datetime.now() - FIRSTJAN).days
        dayForState = 250 if dayAfterMonth < 250 else dayAfterMonth
        self.run_epidemic_calc_district(dayAfterMonth)
        state_stats = self.run_epidemic_calc_state(dayForState)

        Extractor.prepare_state_map_data(state_stats)
        Extractor.prepare_state_wise_Rt(state_stats)
        Extractor.prepare_age_wise_estimation(state_stats, dayForState)

    def cal_pos(self, state_name):
        tot_test,tot_pos=0,0
        testing_data=pd.read_csv('https://api.covid19india.org/csv/latest/statewise_tested_numbers_data.csv')
        state_grp=testing_data.groupby('State')
        for name,grp in state_grp:
            state=grp[['Updated On']]
            state['Total Tested']=grp['Total Tested'].diff()
            state['Positive']=grp['Positive'].diff()
            state['Total Infected']=grp['Positive']
            state.dropna(subset = ["Positive"], inplace=True)
            state=state[len(state)-5:len(state)]
            state=state[state['Total Tested']<100000]
            test=int(state['Total Tested'].sum())
            pos=int(state['Positive'].sum())
            test_pos=round(((pos/test)*100),2)
            tot_test+=test
            tot_pos+=pos
            if name==state_name:
                return test_pos
        if state_name=='India':
            return round(((tot_pos/tot_test)*100),2)
