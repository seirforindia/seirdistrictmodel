from datasync.file_locator import *
import json

class Nodes:

    @classmethod
    def get_district_nodal_config(cls, district):
        node_data = district[['State', 'District', 'Population', 'TN']]
        node_data.columns = ['State', 'node', 'pop', 't0']
        return node_data.to_dict('Records')

    @classmethod
    def get_nodal_config(cls, nodes, states):
        node_config_list = []
        for node in nodes:
            if node["node"] in states.States.to_list():
                state_default_params = states.loc[states.States == node["node"], ["States", "Population", "TN"]]. \
                    rename(columns={"States": "node", "Population": "pop", "TN": "t0"}).to_dict('r')[0]
                state_default_params.update(node)
                if "nodal_param_change" in state_default_params.keys():
                    for param in state_default_params["nodal_param_change"]:
                        param["intervention_day"] = (
                                datetime.strptime(param["intervention_date"], '%m-%d-%Y') - FIRSTJAN).days
                node_config_list.append(state_default_params)
        return node_config_list

    @classmethod
    def get_global_dict(cls, my_dict):
        for intervention in my_dict["param"]:
            intervention["intervention_type"] = "global"
            intervention["intervention_day"] = (
                    datetime.strptime(intervention["intervention_date"], '%m-%d-%Y') - FIRSTJAN).days
        return my_dict

    @classmethod
    def india_node(cls, states):
        return { "node": "India", "pop": 1379426518, 't0': states.TN.min()}

    @classmethod
    def default_global_dict(cls):
        with open('data/global.json') as g :
            raw_dict = json.load(g)
            return cls.get_global_dict(raw_dict)

    @classmethod
    def default_nodal_dict(cls):
        with open('data/nodal.json') as f:
            raw_nodes = json.load(f)
            return raw_nodes