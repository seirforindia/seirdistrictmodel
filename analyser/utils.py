import numpy as np
from datetime import datetime


def json_converter(o):
    if isinstance(o, datetime):
        return o.__str__()
    if isinstance(o, np.ndarray):
        return np.round(o, 2).tolist()
    if isinstance(o, np.int64):
        return int(o)