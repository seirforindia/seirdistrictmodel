import numpy as np
import copy

CFR_div=1
I_mult=1
rate_range=[0,1]
I_range=[0,200]

class SeirConfig:
    def __init__(self, nodal_config, global_config,node='default',
                 pop=39600000,
                 t0=0,
                 no_of_age_groups=4,
                 D_incubation=5.2,
                 D_infectious=2.9,
                 S0=-1,
                 I0=50,
                 R0=0,
                 E0=100,
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
                 D_death=20,
                 D_hospital_lag=5,
                 D_recovery_severe=28.6,
                 D_recovery_mild=11.1,
                 rate_frac=np.array([1]*4),
                 pop_frac=np.array([0.44,0.35,0.15,0.06]),
                 CFR=np.array([0.003, 0.03, 0.12, 0.24])*3,
                 P_SEVERE=np.array([0.05, 0.18, 0.25, 0.50]),
                 rates=2.3,
                 intervention_day = 0,
                 param=[],
                 nodal_param_change=[],
                 ):
        self.node = node
        self.pop = pop
        self.t0 = t0
        self.no_of_age_groups=no_of_age_groups
        self.pop_frac = pop_frac
        self.I0 = np.round(I0*pop_frac) if I0>2 else np.array([0,I0,0,0])
        self.E0 = np.round(E0*pop_frac) if E0>2 else np.array([0,R0,0,0])
        self.rate_frac=rate_frac
        self.CFR = CFR
        self.P_SEVERE = P_SEVERE
        r1 = 3.5
        r2 = 2.5
        r3 = 1.9
        r4 = 1.1
        self.rates=np.array([[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4], [r4, r4, r4, r4]])*pop_frac*np.reshape(rate_frac,[no_of_age_groups,1])*rates/2.3
        self.param = param
        self.nodal_param_change=nodal_param_change
        self.R0 = np.round(R0*pop_frac) if R0>2 else np.array([0,R0,0,0])
        self.S0 = np.round(S0*pop_frac)
        self.delI=np.round(delI*pop_frac) if delI>2 else np.array([0,delI,0,0])
        self.delR=np.round(delR*pop_frac) if delR>2 else np.array([0,delR,0,0])
        self.delS=np.round(delS*pop_frac) if delS>2 else np.array([0,delS,0,0])
        self.delE=np.round(delE*pop_frac) if delE>2 else np.array([0,delE,0,0])
        self.D_incubation = np.array([D_incubation]*no_of_age_groups)
        self.D_infectious = np.array([D_infectious]*no_of_age_groups)
        self.Mild0 = np.array([Mild0]*no_of_age_groups)
        self.Severe0 = np.array([Severe0]*no_of_age_groups)
        self.Severe_H0 = np.array([Severe_H0]*no_of_age_groups)
        self.Fatal0 = np.array([Fatal0]*no_of_age_groups)
        self.R_Mild0 = np.array([R_Mild0]*no_of_age_groups)
        self.R_Severe0 = np.array([R_Severe0]*no_of_age_groups)
        self.R_Fatal0 = np.array([R_Fatal0]*no_of_age_groups)
        self.D_death = np.array([D_death]*no_of_age_groups)
        self.D_hospital_lag = np.array([D_hospital_lag]*no_of_age_groups)
        self.D_recovery_severe = np.array([D_recovery_severe]*no_of_age_groups)
        self.D_recovery_mild = np.array([D_recovery_mild]*no_of_age_groups)
        self.population = pop
        self.intervention_day = intervention_day
        global_config.update(nodal_config)
        self.load_local_config(global_config)
        if "nodal_param_change" in nodal_config.keys():
            self.param = self._merge_dict(self.param,nodal_config["nodal_param_change"])


    def load_local_config(self, local_config):

        local_config_params = {}
        if 'pop_frac' in local_config.keys():
            popfrac=local_config['pop_frac']
            self.rates=np.array(self.rates)*popfrac/self.pop_frac
            self.E0=np.round(np.array(self.E0)*popfrac/self.pop_frac)
            self.I0=np.round(np.array(self.I0)*popfrac/self.pop_frac)
        else:
            popfrac=self.pop_frac
        no_of_agegroups=local_config['no_of_age_groups'] if 'no_of_age_groups' in local_config.keys() else 4

        for key,value in local_config.items():

            if key=='nodal_param_change' or key=='param':
                new_value=[]
                for dictt in value:
                    new={}
                    for k,v in dictt.items():
                        if k=='S0'or k=='E0' or k=='R0' or k=='I0' or k=='delI' or k=='delS' or k=='delR' or k=='delE':
                            v = np.round(v*np.array(popfrac)) if int(v)>2 else np.array([0,v,0,0])
                        elif k=='rates':
                            r1 = 3.5
                            r2 = 2.5
                            r3 = 1.9
                            r4 = 1.1
                            v=np.array([[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4], [r4, r4, r4, r4]])*popfrac*v/2.3
                        elif k!='intervention_day' and type(v)==list:
                            v=np.array(v)
                        new[k]=v
                    new_value.append(new)
                    value=new_value

            elif key=='S0'or key=='E0' or key=='R0' or key=='I0' or key=='delI' or key=='delS' or key=='delR' or key=='delE':
                value = np.round(value*np.array(popfrac)) if int(value)>2 else np.array([0,value,0,0])
                if key=='I0' and ('E0' not in local_config.keys()):
                    self.E0= 2*value
            elif key=='rates':
                r1 = 3.5
                r2 = 2.5
                r3 = 1.9
                r4 = 1.1
                value=np.array([[r2, r3, r3, r4], [r3, r1, r2, r4], [r3, r2, r1, r4], [r4, r4, r4, r4]])*popfrac*value/2.3
            elif (key)!='node' and (key)!='pop' and key!='t0' and key!='no_of_age_groups' and key!= 'intervention_day' and (type(value)==float or type(value)==int):
                value = np.array([value]*no_of_agegroups)
            elif type(value)==list:
                value=np.array(value)
            setattr(self, key, value)



    def _merge_dict(self, param, a):
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

    def clone(self):
        return copy.copy(self)