from analyser.flourish import Flourish
from analyser.seirmodel import SeirModel

def run_model():
    seir_model =  SeirModel()
    seir_model.run_model()
    Flourish.create_flourish_data()