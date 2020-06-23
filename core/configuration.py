import numpy as np
import configparser

config = configparser()
config.read("../config/seir.ini")
SEIR_CONFIG = config['SEIR']


class SeirConfig:
    def __init__(self, nodal_config, global_config, node='default'):
        self.node = node
        self.pop = SEIR_CONFIG['POPULATION']
        self.t0 = SEIR_CONFIG['T0']
        self.no_of_age_groups = SEIR_CONFIG['NO_OF_AGE_GROUPS']
        self.pop_frac = SEIR_CONFIG['POPULATION_FRACTION_DEMOGRAPHICS']
        self.I0 = np.round(SEIR_CONFIG['I0'] * self.pop_frac) if SEIR_CONFIG['I0'] > 2 else np.array(
            [0, SEIR_CONFIG['I0'], 0, 0])
        self.E0 = np.round(SEIR_CONFIG['E0'] * self.pop_frac) if SEIR_CONFIG['E0'] > 2 else np.array(
            [0, SEIR_CONFIG['R0'], 0, 0])
        self.rate_frac = np.array([1]*SEIR_CONFIG['RATE_OF_REDUCTION_FRACTION'])
        self.CFR = SEIR_CONFIG['CASE_FATALITY_RATE']
        self.P_SEVERE = SEIR_CONFIG['HOSPITALIZATION_INFECTION_SEVERE']
        r1 = 3.5
        r2 = 2.5
        r3 = 1.9
        r4 = 1.1
        self.rates = np.array(
            [[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4], [r4, r4, r4, r4]]) * self.pop_frac * np.reshape(
            self.rate_frac, [self.no_of_age_groups, 1]) * SEIR_CONFIG['RATES'] / 2.3
        self.param = SeirConfig['PARAM']
        self.nodal_param_change = SEIR_CONFIG['NODAL_PARAM_CHANGE']
        self.R0 = np.round(SeirConfig['RECOVERY0'] * self.pop_frac) if SeirConfig['RECOVERY0'] > 2 else np.array([0, SeirConfig['RECOVERY0'], 0, 0])
        self.S0 = np.round(SeirConfig['SUSCEPTIBLE0'] * self.pop_frac)
        self.delI = np.round(SEIR_CONFIG['DELI'] * self.pop_frac) if SEIR_CONFIG['DELI'] > 2 else np.array([0, SEIR_CONFIG['DELI'], 0, 0])
        self.delR = np.round(SEIR_CONFIG['DELR'] * self.pop_frac) if SEIR_CONFIG['DELR'] > 2 else np.array([0, SEIR_CONFIG['DELR'], 0, 0])
        self.delS = np.round(SEIR_CONFIG['DELS'] * self.pop_frac) if SEIR_CONFIG['DELS'] > 2 else np.array([0, SEIR_CONFIG['DELS'], 0, 0])
        self.delE = np.round(SEIR_CONFIG['DELE'] * self.pop_frac) if SEIR_CONFIG['DELE'] > 2 else np.array([0, SEIR_CONFIG['DELE'], 0, 0])
        self.D_incubation = np.array([SEIR_CONFIG['LENGTH_INCUBATION']] * self.no_of_age_groups)
        self.D_infectious = np.array([SEIR_CONFIG['DURATION_INFECTIOUS']] * self.no_of_age_groups)
        self.Mild0 = np.array([SEIR_CONFIG['MILD0']] * self.no_of_age_groups)
        self.Severe0 = np.array([SEIR_CONFIG['SEVERE0']] * self.no_of_age_groups)
        self.Severe_H0 = np.array([SEIR_CONFIG['SEVERE_H0']] * self.no_of_age_groups)
        self.Fatal0 = np.array([SEIR_CONFIG['FATAL0']] * self.no_of_age_groups)
        self.R_Mild0 = np.array([SEIR_CONFIG['R_MILD0']] * self.no_of_age_groups)
        self.R_Severe0 = np.array([SEIR_CONFIG['R_SEVERE0']] * self.no_of_age_groups)
        self.R_Fatal0 = np.array(['R_Fatal0'] * self.no_of_age_groups)
        self.D_death = np.array([SEIR_CONFIG['TIME_FROM_INCUBATION_TO_DEATH']] * self.no_of_age_groups)
        self.D_hospital_lag = np.array([SeirConfig['TIME_HOSPITALZATION']] * self.no_of_age_groups)
        self.D_recovery_severe = np.array([SeirConfig['RECOVERY_HOSTIALIZATION_TIME_SEVERE_CASES']] * self.no_of_age_groups)
        self.D_recovery_mild = np.array([SeirConfig['RECOVERY_TIME_MILD_CASES']] * self.no_of_age_groups)
        self.population = SEIR_CONFIG['POPULATION']
        self.intervention_day = SEIR_CONFIG['INVERVENTIONAL_day']
        global_config.update(nodal_config)
        self.load_local_config(global_config)
        if "nodal_param_change" in nodal_config.keys():
            self.param = merge_dict(self.param, nodal_config["nodal_param_change"])

    def load_local_config(self, local_config):

        if 'pop_frac' in local_config.keys():
            popfrac = local_config['pop_frac']
            self.rates = np.array(self.rates) * popfrac / self.pop_frac
            self.E0 = np.round(np.array(self.E0) * popfrac / self.pop_frac)
            self.I0 = np.round(np.array(self.I0) * popfrac / self.pop_frac)
        else:
            popfrac = self.pop_frac
        no_of_agegroups = local_config['no_of_age_groups'] if 'no_of_age_groups' in local_config.keys() else 4

        for key, value in local_config.items():

            if key == 'nodal_param_change' or key == 'param':
                new_value = []
                for dictt in value:
                    new = {}
                    for k, v in dictt.items():
                        if k == 'S0' or k == 'E0' or k == 'R0' or k == 'I0' or k == 'delI' or k == 'delS' or k == 'delR' or k == 'delE':
                            v = np.round(v * np.array(popfrac)) if int(v) > 2 else np.array([0, v, 0, 0])
                        elif k == 'rates':
                            r1 = 3.5
                            r2 = 2.5
                            r3 = 1.9
                            r4 = 1.1
                            v = np.array([[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4],
                                          [r4, r4, r4, r4]]) * popfrac * v / 2.3
                        elif k != 'intervention_day' and type(v) == list:
                            v = np.array(v)
                        new[k] = v
                    new_value.append(new)
                    value = new_value

            elif key == 'S0' or key == 'E0' or key == 'R0' or key == 'I0' or key == 'delI' or key == 'delS' or key == 'delR' or key == 'delE':
                value = np.round(value * np.array(popfrac)) if int(value) > 2 else np.array([0, value, 0, 0])
                if key == 'I0' and ('E0' not in local_config.keys()):
                    self.E0 = 2 * value
            elif key == 'rates':
                r1 = 3.5
                r2 = 2.5
                r3 = 1.9
                r4 = 1.1
                value = np.array(
                    [[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4], [r4, r4, r4, r4]]) * popfrac * value / 2.3
            elif (key) != 'node' and (
                    key) != 'pop' and key != 't0' and key != 'no_of_age_groups' and key != 'intervention_day' and (
                    type(value) == float or type(value) == int):
                value = np.array([value] * no_of_agegroups)
            elif type(value) == list:
                value = np.array(value)
            setattr(self, key, value)

    def getSolution(self, days):

        self.pop = self.population * self.pop_frac
        self.rates = self.rates * np.reshape(self.rate_frac, [self.no_of_age_groups, 1])
        if np.sum(self.S0) <= 0:
            self.S0 = self.pop - self.E0 - self.I0 - self.R0
        self.T, self.S, self.E, self.I, self.R, self.Mild, self.Severe, self.Severe_H, self.Fatal, self.R_Mild, self.R_Severe, self.R_Fatal = list(
            np.arange(self.t0) + 1), [np.array(self.pop)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0

        if len(self.param) != 0:
            for intervention in self.param:
                if self.t0 < intervention['intervention_day']:
                    self.rungeKutta(intervention['intervention_day'])
                    self.t0 = intervention['intervention_day']
                self.__dict__.update(intervention)
                self.I0, self.S0, self.E0, self.R0, self.rates = self.I0 + self.delI, self.S0 + self.delS, self.E0 + self.delE, self.R0 + self.delR, self.rates * np.reshape(
                    self.rate_frac, [self.no_of_age_groups, 1])
                r1 = 3.5
                r2 = 2.5
                r3 = 1.9
                r4 = 1.1
                self.rates = np.array([[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4],
                                       [r4, r4, r4, r4]]) * self.pop_frac * np.reshape(self.rate_frac,
                                                                                       [self.no_of_age_groups, 1])
                self.delI, self.delS, self.delE, self.delR, self.rate_frac = 0, 0, 0, 0, np.array([1] * 4)

        if self.intervention_day < days:
            self.rungeKutta(days)

    def rungeKutta(self, t, n=20, dt=1):
        h = dt / n
        n = int((t - self.t0) / h)
        f0 = np.array(
            [self.S0, self.E0, self.I0, self.R0, self.Mild0, self.Severe0, self.Severe_H0, self.Fatal0, self.R_Mild0,
             self.R_Severe0, self.R_Fatal0])
        f = f0 / self.pop
        for iteration in range(1, n + 1):
            k1 = h * self.dfdt(f)
            k2 = h * self.dfdt(f + 0.5 * k1)
            k3 = h * self.dfdt(f + 0.5 * k2)
            k4 = h * self.dfdt(f + k3)

            f = f + (1.0 / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            t0 = self.t0 + h

            # todo : assign each of the below values to their correesponding T0 values
            if iteration % 20 == 0:
                self.T.append((t0))
                self.S.append((f[0] * self.pop))
                self.E.append((f[1] * self.pop))
                self.I.append((f[2] * self.pop))
                self.R.append((f[3] * self.pop))
                self.Mild.append((f[4] * self.pop))
                self.Severe.append((f[5] * self.pop))
                self.Severe_H.append((f[6] * self.pop))
                self.Fatal.append((f[7] * self.pop))
                self.R_Mild.append((f[8] * self.pop))
                self.R_Severe.append((f[9] * self.pop))
                self.R_Fatal.append((f[10] * self.pop))

        self.T0, self.S0, self.E0, self.I0, self.R0, self.Mild0, self.Severe0, self.Severe_H0, self.Fatal0, self.R_Mild0, self.R_Severe0, self.R_Fatal0 = \
            self.T[-1], self.S[-1], self.E[-1], self.I[-1], self.R[-1], self.Mild[-1], self.Severe[-1], self.Severe_H[
                -1], \
            self.Fatal[-1], self.R_Mild[-1], self.R_Severe[-1], self.R_Fatal[-1]

    def dfdt(self, f):
        S, E, I, R, Mild, Severe, Severe_H, Fatal, R_Mild, R_Severe, R_Fatal = f[0], f[1], f[2], f[3], f[4], f[5], f[6], \
                                                                               f[7], f[8], f[9], f[10]
        beta = self.rates / (self.D_infectious)
        a = 1 / self.D_incubation
        gamma = 1 / self.D_infectious
        p_severe = self.P_SEVERE
        p_fatal = self.CFR
        p_mild = 1 - self.P_SEVERE - self.CFR

        dS = -S * np.dot(beta, I)
        dE = S * np.dot(beta, I) - a * E
        dI = a * E - gamma * I
        dR = gamma * I
        dMild = p_mild * gamma * I - (1 / self.D_recovery_mild) * Mild
        dSevere = p_severe * gamma * I - (1 / self.D_hospital_lag) * Severe
        dSevere_H = (1 / self.D_hospital_lag) * Severe - (1 / self.D_recovery_severe) * Severe_H
        dFatal = p_fatal * gamma * I - (1 / self.D_death) * Fatal
        dR_Mild = (1 / self.D_recovery_mild) * Mild
        dR_Severe = (1 / self.D_recovery_severe) * Severe_H
        dR_Fatal = (1 / self.D_death) * Fatal

        return np.array([dS, dE, dI, dR, dMild, dSevere, dSevere_H, dFatal, dR_Mild, dR_Severe, dR_Fatal])


def merge_dict(param, a):
    merged_list = param + a
    if len(merged_list) != 0:
        res_list = []
        final = []
        for i in range(len(merged_list)):
            if merged_list[i] not in merged_list[i + 1:] and merged_list[i].keys() != 0:
                res_list.append(merged_list[i])
        sorted_list = sorted(res_list, key=lambda k: k['intervention_day'])
        i, j = 0, 1
        while i < len(sorted_list) and j < len(sorted_list):
            if sorted_list[i]['intervention_day'] == sorted_list[j]['intervention_day'] and i != j:
                sorted_list[i].update(sorted_list[j])
                sorted_list.remove(sorted_list[j])
            else:
                i += 1
        return sorted_list
    else:
        return merged_list
