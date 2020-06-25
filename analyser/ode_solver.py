import numpy as np

class ODESolver:
    def __init__(self, model_config):
        self.model_config = model_config

    def getSolution(self, days):

        self.model_config.pop = self.model_config.population * self.model_config.pop_frac
        self.model_config.rates = self.model_config.rates * np.reshape(self.model_config.rate_frac, [self.model_config.no_of_age_groups, 1])
        if np.sum(self.model_config.S0) <= 0:
            self.model_config.S0 = self.model_config.pop - self.model_config.E0 - self.model_config.I0 - self.model_config.R0
        self.model_config.T, self.model_config.S, self.model_config.E, self.model_config.I, self.model_config.R, self.model_config.Mild, self.model_config.Severe, self.model_config.Severe_H, self.model_config.Fatal, self.model_config.R_Mild, self.model_config.R_Severe, self.model_config.R_Fatal = list(
            np.arange(self.model_config.t0) + 1), [np.array(self.model_config.pop)] * self.model_config.t0, [np.array(
            [0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array([0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array(
            [0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array([0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array(
            [0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array([0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array(
            [0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array([0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array(
            [0] * self.model_config.no_of_age_groups)] * self.model_config.t0, [np.array([0] * self.model_config.no_of_age_groups)] * self.model_config.t0

        if len(self.model_config.param) != 0:
            for intervention in self.model_config.param:
                if self.model_config.t0 < intervention['intervention_day']:
                    self._rungeKutta(intervention['intervention_day'])
                    self.model_config.t0 = intervention['intervention_day']
                self.model_config.__dict__.update(intervention)
                self.model_config.I0, self.model_config.S0, self.model_config.E0, self.model_config.R0, self.model_config.rates = self.model_config.I0 + self.model_config.delI, self.model_config.S0 + self.model_config.delS, self.model_config.E0 + self.model_config.delE, self.model_config.R0 + self.model_config.delR, self.model_config.rates * np.reshape(
                    self.model_config.rate_frac, [self.model_config.no_of_age_groups, 1])
                r1 = 3.82
                r2 = 2.54
                r3 = 1.59
                r4 = 0.64
                self.model_config.rates = np.array([[r1, r2, r3, r4], [r2, r1, r3, r4], [r2, r3, r3, r4],
                                       [r4, r4, r4, r4]]) * self.model_config.pop_frac * np.reshape(self.model_config.rate_frac,
                                                                                       [self.model_config.no_of_age_groups, 1])
                r1 = 3.5
                r2 = 2.5
                r3 = 1.9
                r4 = 1.1
                self.model_config.rates = np.array([[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4],
                                       [r4, r4, r4, r4]]) * self.model_config.pop_frac * np.reshape(self.model_config.rate_frac,
                                                                                       [self.model_config.no_of_age_groups, 1])
                self.model_config.delI, self.model_config.delS, self.model_config.delE, self.model_config.delR, self.model_config.rate_frac = 0, 0, 0, 0, np.array([1] * 4)

        if self.model_config.intervention_day < days:
            self._rungeKutta(days)

    def _rungeKutta(self, t, n=20, dt=1):
        # n = Count number of iterations using step size  or
        # step height h
        h = dt / n
        n = int((t - self.model_config.t0) / h)
        # Iterate for number of iterations
        f0 = np.array(
            [self.model_config.S0, self.model_config.E0, self.model_config.I0, self.model_config.R0, self.model_config.Mild0, self.model_config.Severe0, self.model_config.Severe_H0, self.model_config.Fatal0, self.model_config.R_Mild0,
             self.model_config.R_Severe0, self.model_config.R_Fatal0])
        f = f0 / self.model_config.pop
        for iteration in range(1, n + 1):
            k1 = h * self._dfdt(f)
            k2 = h * self._dfdt(f + 0.5 * k1)
            k3 = h * self._dfdt(f + 0.5 * k2)
            k4 = h * self._dfdt(f + k3)

            f = f + (1.0 / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            # Update next value of x
            t0 = self.model_config.t0 + h

            # todo : assign each of the below values to their correesponding T0 values
            if iteration % 20 == 0:
                self.model_config.T.append((t0))
                self.model_config.S.append((f[0] * self.model_config.pop))
                self.model_config.E.append((f[1] * self.model_config.pop))
                self.model_config.I.append((f[2] * self.model_config.pop))
                self.model_config.R.append((f[3] * self.model_config.pop))
                self.model_config.Mild.append((f[4] * self.model_config.pop))
                self.model_config.Severe.append((f[5] * self.model_config.pop))
                self.model_config.Severe_H.append((f[6] * self.model_config.pop))
                self.model_config.Fatal.append((f[7] * self.model_config.pop))
                self.model_config.R_Mild.append((f[8] * self.model_config.pop))
                self.model_config.R_Severe.append((f[9] * self.model_config.pop))
                self.model_config.R_Fatal.append((f[10] * self.model_config.pop))

        self.model_config.T0, self.model_config.S0, self.model_config.E0, self.model_config.I0, self.model_config.R0, self.model_config.Mild0, self.model_config.Severe0, self.model_config.Severe_H0, self.model_config.Fatal0, self.model_config.R_Mild0, self.model_config.R_Severe0, self.model_config.R_Fatal0 = \
            self.model_config.T[-1], self.model_config.S[-1], self.model_config.E[-1], self.model_config.I[-1], self.model_config.R[-1], self.model_config.Mild[-1], self.model_config.Severe[-1], self.model_config.Severe_H[
                -1], \
            self.model_config.Fatal[-1], self.model_config.R_Mild[-1], self.model_config.R_Severe[-1], self.model_config.R_Fatal[-1]

    def _dfdt(self, f):
        S, E, I, R, Mild, Severe, Severe_H, Fatal, R_Mild, R_Severe, R_Fatal = f[0], f[1], f[2], f[3], f[4], f[5], f[6], \
                                                                               f[7], f[8], f[9], f[10]
        beta = self.model_config.rates / (self.model_config.D_infectious)
        a = 1 / self.model_config.D_incubation
        gamma = 1 / self.model_config.D_infectious
        p_severe = self.model_config.P_SEVERE
        p_fatal = self.model_config.CFR
        p_mild = 1 - self.model_config.P_SEVERE - self.model_config.CFR

        dS = -S * np.dot(beta, I)
        dE = S * np.dot(beta, I) - a * E
        dI = a * E - gamma * I
        dR = gamma * I
        dMild = p_mild * gamma * I - (1 / self.model_config.D_recovery_mild) * Mild
        dSevere = p_severe * gamma * I - (1 / self.model_config.D_hospital_lag) * Severe
        dSevere_H = (1 / self.model_config.D_hospital_lag) * Severe - (1 / self.model_config.D_recovery_severe) * Severe_H
        dFatal = p_fatal * gamma * I - (1 / self.model_config.D_death) * Fatal
        dR_Mild = (1 / self.model_config.D_recovery_mild) * Mild
        dR_Severe = (1 / self.model_config.D_recovery_severe) * Severe_H
        dR_Fatal = (1 / self.model_config.D_death) * Fatal

        return np.array([dS, dE, dI, dR, dMild, dSevere, dSevere_H, dFatal, dR_Mild, dR_Severe, dR_Fatal])

    def upload_model_config(self, model_config):
        self.model_config = model_config