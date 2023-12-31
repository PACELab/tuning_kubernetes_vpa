import os
import sys
import argparse
from timeit import default_timer as timer
import pickle
import yaml

import crossplane
import pandas as pd

# import carver
#import helper
#import bayesopt
# import hyperopt_algos
# import pso
# import dds
#import pbr
# import ucb
# import genetic_opt
#import cb
# import config_to_docker_compose


def update_manifest_file(source, destination, args_list):
    """
    Update a manifest args field of the manifest file.
    """
    data = load_manifest_file(
        source, yaml_index=1)  # yaml_index is the index of the yaml docs in the file
    # print(data["spec"]["template"]["spec"]["containers"][0]["args"])
    print(data["spec"]["template"]["spec"]["containers"][0])
    data["spec"]["template"]["spec"]["containers"][0]["args"] = list(map(str,args_list))
    print(data["spec"]["template"]["spec"]["containers"][0])
    write_manifest_file(destination, data)


def write_manifest_file(manifest_file, data=""):
    """
    Write a manifest file. If data is not provided, creates an empty file.
    """
    with open(manifest_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


# yaml_index is the index of the yaml docs in the file
def load_manifest_file(manifest_file, yaml_index=0):
    """
    Load a manifest file. If the file contains multiple yaml docs, yaml_index is the index of the docs to load.
    """
    with open(manifest_file) as f:
        data = list(yaml.load_all(f, Loader=yaml.FullLoader))

    return data[yaml_index]


def memcached_config(template_path, destination, microservice, microservice_df):
    param_prefix = "-"
    args_list = []
    for _, row in microservice_df.iterrows():
        args_list.append(param_prefix + row["parameter"])
        args_list.append(row["value"])

    update_manifest_file(os.path.join(template_path, f"{microservice}.yaml"), os.path.join(
        destination, f"{microservice}.yaml"), args_list)


def mongo_config(template_path, destination, microservice, microservice_df):
    param_prefix = "--"
    param_prefix_command = {"wiredTigerConcurrentWriteTransactions": "--setParameter",
                            "wiredTigerConcurrentReadTransactions": "--setParameter"}  # default is "--"
    param_value_separator = {
        "wiredTigerConcurrentWriteTransactions": "=", "wiredTigerConcurrentReadTransactions": "="}

    args_list = []

    for _, row in microservice_df.iterrows():
        if row["parameter"] in param_prefix_command:
            args_list.append(param_prefix_command[row["parameter"]])
            args_list.append(
                row['parameter'] + param_value_separator[row['parameter']] + str(row['value']))
        else:
            args_list.append(param_prefix + row["parameter"])
            args_list.append(row['value'])
    update_manifest_file(os.path.join(template_path, f"{microservice}.yaml"), os.path.join(
        destination, f"{microservice}.yaml"), args_list)


def mysql_config(template_path, microservice, microservice_df):
    pass


def redis_config(template_path, destination, microservice, microservice_df):
    param_prefix = "--"
    value_suffix_dict = {"maxmemory": "mb"}
    args_list = []

    for _, row in microservice_df.iterrows():
        args_list.append(param_prefix + row["parameter"])
        value_suffix = value_suffix_dict.get(row["parameter"], "")
        args_list.append(f"{row['value']}{value_suffix}")

    update_manifest_file(os.path.join(template_path, f"{microservice}.yaml"), os.path.join(
        destination, f"{microservice}.yaml"), args_list)


def nginx_config(app, destination, microservice, microservice_df, nginx_template_path, nginx_remote_destination, workers):
    """
    Update the nginx config file with the new configuration.
    Copies the config file to all the worker nodes.
    """
    parameters = microservice_df["parameter"].tolist()

    payload = crossplane.parse(nginx_template_path)

    payload_content = payload["config"][0]["parsed"]

    # loop over the dictionary to find the parameters and update their "args" field.
    for index, dict_element in enumerate(payload_content):
        if "block" in dict_element:
            if payload_content[index]["block"][0]["directive"] == "worker_connections":
                payload_content[index]["block"][0]["args"] = [str(
                    microservice_df[microservice_df.parameter == "worker_connections"]["value"].values[0])]
        if dict_element["directive"] == "worker_processes":
            payload_content[index]["args"] = [str(
                microservice_df[microservice_df.parameter == "worker_processes"]["value"].values[0])]
        # this has to be explicitly added in the template file.
        if "threads" in parameters and "max_queue" in parameters:
            if dict_element["directive"] == "thread_pool":
                payload_content[index]["args"] = ["thread1", f"threads={microservice_df[microservice_df.parameter == 'threads']['value'].values[0]}",
                                                  f"max_queue={microservice_df[microservice_df.parameter == 'max_queue']['value'].values[0]}"]

    output = crossplane.build(payload_content)
    with open(os.path.join(destination,"k8-nginx.conf"), "w") as f:
        f.write(output)

    for worker in workers:
        continue
        #scp_helper(template_path, microservice, microservice_df, worker)


def service_config(services_group, workers, services_parameter_destination):
    """
    Format:
    <microservice>-service_io_threads,<>
    <microservice>-service_worker_threads,<>
    """
    services_config_list = []
    for _, row in services_group.iterrows():
        services_config_list.append(f"{row['parameter']},{row['value']}")

    print("\n".join(services_config_list))

    # write to experiment folder and transfer to worker nodes in the correct directory
    for worker in workers:
        continue
        #scp_helper(template_path, microservice, microservice_df, worker)


def update_right_sizing_parameters(microservice, microservice_df):
    pass


def create_manifest_files(parameters_file, config, workers, app="SN", right_size=False):
    # create manifest files and save them in the experiment folder.
    # TODO: copy all the files and modify ones that need to be.

    # TODO: only subset - dimensionality reduction

    nginx_template_path = "nginx_config/sn-k8-nginx.conf"
    nginx_remote_destination = ""
    destination = "delete/test"  # get parameter
    manifest_file_template = "delete/"
    services_parameter_destination = ""
    parameters_meta = pd.read_csv(parameters_file)
    parameters_meta["value"] = config

    # TODO: REMOVE THIS. ONLY FOR TESTING
    parameters_meta["value"] = parameters_meta["step"]

    application_parameters_meta = parameters_meta[parameters_meta.layer == "application"].drop(
        "layer", axis=1)
    microservices_group = application_parameters_meta.groupby("microservice")

    for microservice, microservice_df in microservices_group:
        if microservice_df.iloc[0]["microservice_type"] == "nginx":
            nginx_config(app, destination, microservice, microservice_df, nginx_template_path, nginx_remote_destination, workers)
        elif microservice_df.iloc[0]["microservice_type"] == "memcached":
            memcached_config(manifest_file_template, destination, microservice, microservice_df)
        elif microservice_df.iloc[0]["microservice_type"] == "mongo":
            mongo_config(manifest_file_template, destination, microservice, microservice_df)
        elif microservice_df.iloc[0]["microservice_type"] == "redis":
            redis_config(manifest_file_template, destination, microservice, microservice_df)
        elif microservice_df.iloc[0]["microservice_type"] == "mysql":
            mysql_config(manifest_file_template, destination, microservice, microservice_df)

    services_group = application_parameters_meta[application_parameters_meta.microservice_type == "service"]
    service_config(services_group, workers, services_parameter_destination)

    right_sizing_parameters_meta = parameters_meta[parameters_meta.layer == "right_sizing"].drop(
        "layer", axis=1)
    microservices_group = right_sizing_parameters_meta.groupby("microservice")
    for microservice, microservice_df in microservices_group:
        update_right_sizing_parameters(microservice, microservice_df)


def save_metrics():
    pass


def save_logs():
    pass


def generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, app, result_folder, cluster_config_dir, client, rps_list, iterations, cluster_number):
    total_time = 0
    number_iterations = 0
    while(not approach_instance.stop_config_generation("dummy")):

        start = timer()
        config = approach_instance.next_config()
        total_time += timer() - start
        number_iterations += 1
        helper.write_app_config_csv(parameter_csv_path, configuration_csv_path,
                                    approach_instance.current_config_index, config, app_config_dir, app)
        objective_function_value = helper.run_config(result_folder, app_config_dir, approach_instance.current_config_index,
                                                     cluster_config_dir, version, app, client, rps_list, iterations, cluster_number)
        approach_instance.analysis(objective_function_value)
    print("Execution per iteration %f" % (total_time/number_iterations))


def create_config_directory(config_dir, app, app_config_dir, dim_red):
    template_dict = {"SN": "sn-%s-temp", "HR": "hr-%s-temp",
                     "MM": "mm-%s-temp", "TT": "tt-%s-temp"}
    os.system("mkdir %s" % app_config_dir)
    os.system("cp -r %s/* %s/" % (os.path.join(config_dir,
              template_dict[app] % dim_red), app_config_dir))


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_folder", help="The folder where the details of the application are present")
    parser.add_argument(
        "main_version", help="The name for this round of experiments")
    parser.add_argument("app", help="The application being used", choices=[
                        "SN", "MM", "HR", "TT"])
    parser.add_argument(
        "cluster_number", help="The cluster on which the experiments are to be run.", choices=[1, 2], type=int)
    parser.add_argument(
        "approach", help="The optimization algorithm to be used")
    parser.add_argument(
        "--client", help="The IP of the client machine", default="130.245.127.132")
    parser.add_argument("--rps_list", "-r", "-R",
                        help="The rps list at which experiments are to be run", nargs="+", type=int)
    parser.add_argument("--experiment_iterations", "-ei",
                        help="The number of times the experiment is repeated for a given algorithm and config (0th iteration is run for cache warm-up", default=1, type=int)
    parser.add_argument("--model_iterations", "-mi",
                        help="The number of iterations the algorithm is run in each sequence", default=12, type=int)
    parser.add_argument("--sequence_count", "-sc",
                        help="The number of times the algorithm is rerun", default=2, type=int)
    parser.add_argument("--start_sequence", "-ss",
                        help="Starting sequence number", default=1, type=int)
    parser.add_argument("--dimensionality_reduction", "-d",
                        help="The dimensionality reduction method used", default="critical_path")
    parser.add_argument(
        "--acq_func", "-a", help="The acquisition function to be used with Bayesian methods", default="EI")
    parser.add_argument("--experiment_duration", "-ed",
                        help="The duration of the online experiment in minutes", default="60")
    parser.add_argument("--warmup_duration", "-wd",
                        help="The duration of the warump in minutes", default="30")
    parser.add_argument("--init", action="store_true",
                        help="Initialize the algorithm with user supplied points instead of library generated random samples.")
    parser.add_argument("--test", action="store_true",
                        help="Temporary flags that is used to test a feature conditionally.")
    parser.add_argument("--online", action="store_true",
                        help="If passed, the experiment is run online")
    parser.add_argument("--monitoring_interval",
                        help="The interval at which the config is changed", default="3")
    return parser.parse_args()


def online_deploy_app(args, result_folder, app_config_dir, app_config_iteration, cluster_config_dir, version):
    """
    """
    config_to_docker_compose.create_docker_compose_files(app_config_dir+"/"+str(
        app_config_iteration)+"_cluster.csv", cluster_config_dir, version, args.app, args.client, app_config_iteration, args.cluster_number)
    host_mapping = {}
    iterations = float(
        args.experiment_duration)//float(args.monitoring_interval)

    with open(cluster_config_dir+"/" + version + "/host_roles.pkl", "rb") as host_roles_f:
        host_mapping = pickle.load(host_roles_f)
    helper.clean_and_deploy_app(cluster_config_dir, version, args.app,
                                args.cluster_number, host_mapping)


if __name__ == "__main__":
    # percentile_across_requests("/home/ubuntu/uservices/uservices-perf-analysis/results/first_exp/v0_rps100/i0","SN")
    # collect_stats("/home/ubuntu/uservices/uservices-perf-analysis/results","v11",0,"SN",[400],3)
    #analysis("/home/ubuntu/uservices/uservices-perf-analysis/results", "configs/first_exp", 15, "first_exp", "SN", [450,500])
    args = argument_parser()
    import random
    create_manifest_files("../configs/sn_parameters.csv",
                          random.sample(range(1, 100), 89), [])
    sys.exit()
    app_file_suffix = {"SN": "social_networking", "MM": "media_microservices",
                       "HR": "hotel_reservation", "TT": "train_ticket"}
    app_folder_dict = {"SN": "socialNetwork", "MM": "mediaMicroservices",
                       "HR": "hotelReservation", "TT": "trainTicket"}
    parameter_csv_file = app_file_suffix[args.app]+"_parameters.csv"
    configuration_csv_file = app_file_suffix[args.app] + "_config.csv"
    result_folder = "/home/ubuntu/uservices/uservices-perf-analysis/results"

    cluster_config_dir = "../DeathStarBench/%s/cluster_setups" % app_folder_dict[args.app]

    for sequence_number in range(args.start_sequence, args.sequence_count+1):
        version = args.main_version + "-%d" % (sequence_number)
        app_config_dir = os.path.join(args.config_folder, version)
        create_config_directory(
            args.config_folder, args.app, app_config_dir, args.dimensionality_reduction)
        # list of parameters, their ranges, etc
        parameter_csv_path = os.path.join(app_config_dir, parameter_csv_file)
        # a template of the app deployment config
        configuration_csv_path = os.path.join(
            app_config_dir, configuration_csv_file)
        if args.online:
            online_deploy_app(args, result_folder, app_config_dir,
                              0, cluster_config_dir, version)

            # if args.approach == "default":
            #    helper.run_online_config(result_folder, app_config_dir, 0, cluster_config_dir, version, args.app, args.client, args.rps_list,
            #                  args.experiment_iterations, args.cluster_number, collect_jaeger=True)

        elif args.approach == "default":
            helper.run_config(result_folder, app_config_dir, 0, cluster_config_dir, version, args.app, args.client, args.rps_list,
                              args.experiment_iterations, args.cluster_number, collect_jaeger=True)  # run the config without any changes.

        elif args.approach == "default-dsb":
            helper.run_config(result_folder, app_config_dir, 0, cluster_config_dir, version, args.app, args.client, args.rps_list,
                              args.experiment_iterations, args.cluster_number, collect_jaeger=True)  # run the config without any changes.

        elif args.approach == "carver":
            approach_instance = carver.Carver(
                parameter_csv_path, args.rps_list, args.iterations, current_config_index=-1, num_samples=8, num_buckets=8)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)

        elif args.approach == "dds":
            approach_instance = dds.DDS(
                args, parameter_csv_path, sequence_number, r=0.2)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)

        elif args.approach.startswith("bayesopt"):
            approach_instance = bayesopt.BayesianOptimization(
                args, sequence_number)
            approach_instance.optimize()

        elif args.approach == "tpe":
            approach_instance = hyperopt_algos.HyperOptAlgos(
                args, sequence_number)
            approach_instance.optimize()

        elif args.approach == "sa":
            approach_instance = hyperopt_algos.HyperOptAlgos(
                args, sequence_number)
            approach_instance.optimize()
        elif args.approach == "pso":
            approach_instance = pso.Pso(args, sequence_number)
            approach_instance.optimize()
        elif args.approach == "genetic":
            approach_instance = genetic_opt.GeneticOpt(args, sequence_number)
            approach_instance.optimize()
        elif args.approach == "hybrid":
            dds_iter = 6
            args.model_iterations = dds_iter
            approach_instance = dds.DDS(
                args, parameter_csv_path, sequence_number, r=0.2)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
            bo_iter = 15
            args.model_iterations = bo_iter
            approach_instance = bayesopt.BayesianOptimization(
                args, sequence_number, current_model_iteration=dds_iter)
            approach_instance.optimize()
        elif args.approach == "pbr":
            approach_instance = pbr.PBR(args, parameter_csv_path, configuration_csv_path,
                                        app_config_dir, result_folder, cluster_config_dir, version, sequence_number)
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
        elif args.approach == "ucb":
            approach_instance = ucb.UCB_MAB(args, parameter_csv_path, )
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
        elif args.approach == "cb":
            approach_instance = cb.CBZO(args, parameter_csv_path, )
            generic_method(approach_instance, parameter_csv_path, configuration_csv_path, app_config_dir, args.app,
                           result_folder, cluster_config_dir, args.client, args.rps_list, args.experiment_iterations, args.cluster_number)
        else:
            print("Invalid approach")
            sys.exit(0)
        try:
            os.mkdir(app_config_dir)
        except FileExistsError as e:
            print("Error %s occured while trying to create the version directory %s" % (
                e, app_config_dir))
