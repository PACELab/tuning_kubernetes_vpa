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
    current_iteration = -1
    while(not approach_instance.stop_config_generation("dummy")):
        start = timer()
        config = approach_instance.next_config()
        print("config returned from approach_instance.next_config()")
        print(config)
        total_time += timer() - start
        current_iteration += 1
        objective_function_value = helper.get_reward(args, experiment_version_folder, current_iteration, config)
        #objective_function_value = random.randint(80,100)
        approach_instance.analysis(objective_function_value)
    print("Execution per iteration %f" % (total_time/current_iteration))


if __name__ == "__main__":
    args = arguments.argument_parser()
    experiment_version_folder = os.path.join(args.results_folder , args.experiment_type + "-" + args.experiment_version)
    helper.create_folder_p(experiment_version_folder)
    #TODO: copy all files to the expriment_version_folder to get back the exact results.
    for sequence_number in range(args.start_sequence, args.sequence_count+1):
        if args.approach == "PBR":
            approach_instance = pbr.PBR(args, experiment_version_folder, sequence_number, "configs/vpa_parameters.csv")
            run_algorithm(args)
        elif args.approach == "CB":
            approach_instance = cb.CBZO(args, experiment_version_folder, "configs/vpa_parameters.csv")
            run_algorithm(args)
        elif args.approach.startswith("bayesopt"):
            approach_instance = bayesopt.BayesianOptimization(args, experiment_version_folder)
            approach_instance.optimize()
