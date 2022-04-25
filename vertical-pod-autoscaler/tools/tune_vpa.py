import os
from timeit import default_timer as timer
import random

import helper
import pbr
import cb
import bayesopt
import arguments

def run_algorithm(args):
    total_time = 0
    number_iterations = 0
    while(not approach_instance.stop_config_generation("dummy")):
        start = timer()
        config = approach_instance.next_config()
        total_time += timer() - start
        number_iterations += 1
        objective_function_value = helper.get_reward(args, number_iterations, config)
        #objective_function_value = random.randint(1,10)
        approach_instance.analysis(objective_function_value)
    print("Execution per iteration %f" % (total_time/number_iterations))


if __name__ == "__main__":
    args = arguments.argument_parser()
    for sequence_number in range(args.start_sequence, args.sequence_count+1):
        if args.approach == "PBR":
            approach_instance = pbr.PBR(args, sequence_number, "configs/vpa_parameters.csv")
            run_algorithm(args)
        elif args.approach == "CB":
            approach_instance = cb.CBZO(args, "configs/vpa_parameters.csv")
            run_algorithm(args)
        elif args.approach.startswith("bayesopt"):
            approach_instance = bayesopt.BayesianOptimization(args)
            approach_instance.optimize()
