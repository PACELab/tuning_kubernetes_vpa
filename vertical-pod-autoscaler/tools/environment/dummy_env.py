import random

def take_action(args, model_iteration, action):
    return -random.uniform(1,100)

def next_observation(args):
    """
    1) CPU and memory usage in % of each microservice in sequence
    2) CPU and memory usage in % of the node
    3) RPS
    4) Connections
    5) Request composition array in % (three values)
    """
    observation = []
    observation += random.sample(range(0, 100), 29 * 2)
    observation += random.sample(range(0, 100), 1 * 2)
    observation += [3200]
    observation += [1600]
    observation += [60,30,10]
    return observation