import numpy as np
from scrap import global_dict

class SeirConfig:
    def __init__(self, nodal_config, global_config=global_dict, node='default',
                 pop=39600000,  # pop = Total population
                 t0=0,  # t0 = offset
                 no_of_age_groups=4,  # No of age groups = 4 by default
                 D_incubation=5.2,  # D_incubation = Length of incubation period
                 D_infectious=2.9,  # D_infectious = Duration patient is infectious
                 S0=-1,  # Put S0 = -1 if not adding value explicitely . Then S0 = Pop -I0-R0-E0
                 I0=50,  # I0 = Initial number of Infectious persons (Number of infections actively circulating)
                 R0=0,
                 # R0 = Initial number of Removed persons (Population no longer infectious due to isolation or immunity)
                 E0=100,  # E0 = Initial number of Exposed persons (Number of infections actively circulating)
                 delI=0,
                 delS=0,
                 delR=0,
                 delE=0,
                 Mild0=0,
                 Severe0=0,
                 Severe_H0=0,
                 Fatal0=0,
                 R_Mild0=0,
                 R_Severe0=0,
                 R_Fatal0=0,
                 D_death=20,  # D_death : Time from end of incubation to death
                 D_hospital_lag=5,  # D_hospital_lag : time_to_hospitalization
                 D_recovery_severe=28.6,  # D_recovery_severe : Length of hospital stay
                 D_recovery_mild=11.1,  # D_recovery_mild : Recovery time for mild cases
                 rate_frac=np.array([1] * 4),  # Array | (1-Rate of reduction)
                 pop_frac=np.array([0.3, 0.35, 0.2, 0.15]),  # pop_frac : population frac of different age groups
                 CFR=np.array([0.001, 0.01, 0.04, 0.08]) * 3,  # CFR : Case Fatality Rate
                 P_SEVERE=np.array([0.05, 0.15, 0.30, 0.75]),
                 # P_SEVERE : Hospitalization Rate (Fraction of infected population admitted to the hospital)
                 r1=3.82,
                 r2=2.54,
                 r3=1.59,
                 r4=0.64,
                 #  param =[{"intervention_day":97,"rate_frac":np.array([0.2]*4)}],
                 intervention_day=0,
                 param=[],
                 nodal_param_change=[], ):
        self.node = node
        self.pop = pop
        self.population = pop
        self.t0 = t0
        self.no_of_age_groups = no_of_age_groups
        self.pop_frac = pop_frac
        self.I0 = np.round(I0 * pop_frac) if I0 > 2 else np.array([0, I0, 0, 0])
        self.E0 = np.round(E0 * pop_frac) if E0 > 2 else np.array([0, R0, 0, 0])
        self.rate_frac = rate_frac
        self.CFR = CFR
        self.P_SEVERE = P_SEVERE
        self.rates = np.array([[r1, r2, r3, r4], [r2, r1, r3, r4], [r2, r3, r3, r4],
                               [r4, r4, r4, r4]]) * pop_frac * rate_frac  # Measure of contagiousness
        self.param = merge_dict(param, nodal_param_change)
        self.R0 = np.round(R0 * pop_frac) if R0 > 2 else np.array([0, R0, 0, 0])
        self.S0 = np.round(S0 * pop_frac)
        self.delI = np.round(delI * pop_frac) if delI > 2 else np.array([0, delI, 0, 0])
        self.delR = np.round(delR * pop_frac) if delR > 2 else np.array([0, delR, 0, 0])
        self.delS = np.round(delS * pop_frac) if delS > 2 else np.array([0, delS, 0, 0])
        self.delE = np.round(delE * pop_frac) if delE > 2 else np.array([0, delE, 0, 0])
        self.D_incubation = np.array([D_incubation] * no_of_age_groups)
        self.D_infectious = np.array([D_infectious] * no_of_age_groups)
        self.Mild0 = np.array([Mild0] * no_of_age_groups)
        self.Severe0 = np.array([Severe0] * no_of_age_groups)
        self.Severe_H0 = np.array([Severe_H0] * no_of_age_groups)
        self.Fatal0 = np.array([Fatal0] * no_of_age_groups)
        self.R_Mild0 = np.array([R_Mild0] * no_of_age_groups)
        self.R_Severe0 = np.array([R_Severe0] * no_of_age_groups)
        self.R_Fatal0 = np.array([R_Fatal0] * no_of_age_groups)
        self.D_death = np.array([D_death] * no_of_age_groups)
        self.D_hospital_lag = np.array([D_hospital_lag] * no_of_age_groups)
        self.D_recovery_severe = np.array([D_recovery_severe] * no_of_age_groups)
        self.D_recovery_mild = np.array([D_recovery_mild] * no_of_age_groups)
        self.intervention_day = intervention_day
        global_config.update(nodal_config)
        self.load_local_config(global_config)

    def load_local_config(self, local_config):
        ratefrac = local_config['rate_frac'] if 'rate_frac' in local_config.keys() else self.rate_frac
        if 'pop_frac' in local_config.keys():
            popfrac = local_config['pop_frac']
            self.rates = np.array(self.rates) * self.rate_frac * popfrac / self.pop_frac
            self.E0 = np.round(np.array(self.E0) * popfrac / self.pop_frac)
            self.I0 = np.round(np.array(self.I0) * popfrac / self.pop_frac)
        else:
            popfrac = self.pop_frac
        no_of_agegroups = local_config['no_of_age_groups'] if 'no_of_age_groups' in local_config.keys() else 4

        for key, value in local_config.items():
            if key == 'nodal_param_change' or key == 'param':
                pass
            elif type(value) == list:
                value = np.array(value)
            elif key == 'S0' or key == 'E0' or key == 'R0' or key == 'I0' or key == 'delI' or key == 'delS' or key == 'delR' or key == 'delE':
                value = np.round(value * np.array(popfrac)) if int(value) > 2 else np.array([0, value, 0, 0])
                if key == 'I0' and 'E0' not in local_config.keys():
                    setattr(self, 'E0', 2 * value) if value[2] > 1 else setattr(self, 'E0',
                                                                                np.array([0] * no_of_agegroups))
            elif (key) != 'node' and (key) != 'pop' and key != 't0' and key != 'no_of_age_groups' and (
                    type(value) == float or type(value) == int):
                value = np.array([value] * no_of_agegroups)

            setattr(self, key, value)

    def getSolution(self, days):
        self.T, self.S, self.E, self.I, self.R, self.Mild, self.Severe, self.Severe_H, self.Fatal, self.R_Mild, self.R_Severe, self.R_Fatal = list(
            np.arange(self.t0) + 1), [np.array(self.pop)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0, [np.array(
            [0] * self.no_of_age_groups)] * self.t0, [np.array([0] * self.no_of_age_groups)] * self.t0
        self.pop = self.population * self.pop_frac
        self.rates = self.rates * np.reshape(self.rate_frac, [self.no_of_age_groups, 1])
        if np.sum(self.S0) <= 0:
            self.S0 = self.pop - self.E0 - self.I0 - self.R0

        if len(self.param) != 0:
            for intervention in self.param:
                if self.t0 < intervention['intervention_day']:
                    self.rungeKutta(intervention['intervention_day'])
                    self.t0 = intervention['intervention_day']
                self.__dict__.update(intervention)
                self.I0, self.S0, self.E0, self.R0, self.rates = self.I0 + self.delI, self.S0 + self.delS, self.E0 + self.delE, self.R0 + self.delR, self.rates * np.reshape(
                    self.rate_frac, [self.no_of_age_groups, 1])

        if self.intervention_day < days:
            self.rungeKutta(days)

    def rungeKutta(self, t, n=20, dt=1):
        # n = Count number of iterations using step size  or
        # step height h
        h = dt / n
        n = int((t - self.t0) / h)
        # Iterate for number of iterations
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
            # Update next value of x
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
        self.T[-1], self.S[-1], self.E[-1], self.I[-1], self.R[-1], self.Mild[-1], self.Severe[-1], self.Severe_H[-1], \
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
