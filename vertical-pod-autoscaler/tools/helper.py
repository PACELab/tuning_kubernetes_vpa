import re
import sys
from importlib_metadata import version
from numpy import percentile
import yaml
import os
import subprocess
import datetime

import pandas as pd
import numpy as np


import vpa_deployment
import arguments

loads = []
per_load_duration = []


def get_init_points_default():
    return ([5.68, 0.28, 418], 5.88)  # reward used it deficit + 1 * half-life


def generate_workload_sn(version_folder, experiment_version, total_duration, workload_type, new_samples, half_life, n_load_changes=1):
    n_threads = 2
    n_connections = 4
    duration = 120
    port = 8080
    frontend_cluster_ip = ""
    compose_rps = 50
    home_rps = 350
    user_rps = 150
    percentile = 95
    wrk2_folder = "/home/ubuntu/uservices/uservices-perf-analysis"


    os.system("kubectl apply -f /home/ubuntu/firm/benchmarks/1-social-network/k8s-yaml/social-network-ns.yaml")
    os.system("kubectl apply -f /home/ubuntu/firm/benchmarks/1-social-network/k8s-yaml/")

    os.system("sleep 120")

    p = subprocess.run(f"kubectl get svc nginx-thrift -n social-network -ojsonpath='{{.spec.clusterIP}}'", stdout=subprocess.PIPE, shell=True)
    print(p)
    frontend_cluster_ip = p.stdout.decode("ascii").strip()
    print("Frontend cluster IP", frontend_cluster_ip)

    os.system(f"{wrk2_folder}/wrk2/wrk -D exp -t {n_threads} -c {n_connections} -d {duration} -P {version_folder}/compose_latencies.txt -L -s {wrk2_folder}/wrk2/scripts/social-network/compose-post.lua http://{frontend_cluster_ip}:{port}/wrk2-api/post/compose -R {compose_rps} > {version_folder}/compose.log &")
    os.system(f"{wrk2_folder}/wrk2/wrk -D exp -t {n_threads} -c {n_connections} -d {duration} -P {version_folder}/home_latencies.txt -L -s {wrk2_folder}/wrk2/scripts/social-network/read-home-timeline.lua http://{frontend_cluster_ip}:{port}/wrk2-api/post/compose -R {home_rps} > {version_folder}/home.log &")
    os.system(f"{wrk2_folder}/wrk2/wrk -D exp -t {n_threads} -c {n_connections} -d {duration} -P {version_folder}/user_latencies.txt -L -s {wrk2_folder}/wrk2/scripts/social-network/read-user-timeline.lua http://{frontend_cluster_ip}:{port}/wrk2-api/post/compose -R {user_rps} > {version_folder}/user.log &")
    
    os.system(f"sleep {duration+30}")
    reward = subprocess.run(f"cat {version_folder}/*_latencies.txt | datamash perc:{percentile} 1 > {version_folder}/cost", stdout=subprocess.PIPE, shell=True)

    try:
        # microseconds to milliseconds
        reward = float(reward.stdout)/1000
    except:
        # TODO: send email
        reward = 10000.0
    sys.exit()
    os.system("kubectl delete -f /home/ubuntu/firm/benchmarks/1-social-network/k8s-yaml/")
    os.system("kubectl delete -f /home/ubuntu/firm/benchmarks/1-social-network/k8s-yaml/social-network-ns.yaml")
    write_n_vpa_evictions(version_folder)

    return reward


def generate_workload_nginx(version_folder, experiment_version, total_duration, workload_type, new_samples, half_life, n_load_changes=1):
    global loads
    global per_load_duration
    threads = 2
    clients = 100
    total_duration = int(total_duration)

    if new_samples:
        if workload_type == "diurnal":
            #loads = np.random.normal(2000, 200, n_load_changes)
            loads = [9985, 10145,  9894, 10127]
            per_load_duration = [total_duration //
                                 n_load_changes] * n_load_changes
        elif workload_type == "bursty":
            BURST_PERIOD = 300  # seconds
            per_load_duration = [780, 120, 780, 120, 900,
                                 900, 780, 120, 900, 120, 780, 120, 780]
            per_load_duration = [600, 300, 600, 300, 900, 300, 600]
            bursty_loads = np.random.normal(
                20000, 20, len(per_load_duration) - n_load_changes)
            regular_loads = np.random.normal(2000, 200, len(per_load_duration))
            burst_load_indices = []
            for i, value in enumerate(per_load_duration):
                if value == BURST_PERIOD:
                    burst_load_indices.append(i)
            loads = regular_loads
            for i, burst_rank in enumerate(burst_load_indices):
                loads[burst_rank] = bursty_loads[i]
        else:  # random
            #loads = np.random.normal(2000, 200, n_load_changes)
            loads = [10000]
            per_load_duration = [total_duration //
                                 n_load_changes] * n_load_changes

    # clean a bit
    loads = list(map(int, loads))
    expected_throughput = list([i*j for i, j in zip(loads, per_load_duration)])

    with open(os.path.join(version_folder, "workload_details.txt"), "w") as f:
        f.write(",".join(map(str, loads)))
        f.write("\n")
        f.write(",".join(map(str, per_load_duration)))
    command_script_f = open(os.path.join(version_folder, "commands.sh"), "w")
    vpa = "nginx-vpa-%s" % experiment_version
    vpa_file = vpa + ".yaml"
    vpa_file_path = os.path.join(version_folder, vpa_file)
    deployment = "nginx-deployment-%s" % experiment_version
    deployment_file = deployment + ".yaml"
    deployment_file_path = os.path.join(version_folder, deployment_file)
    subprocess.run("kubectl apply -f %s" % vpa_file_path, shell=True)
    subprocess.run("kubectl apply  -f %s" %
                   deployment_file_path, shell=True)
    subprocess.run(
        "kubectl expose deployment %s --type=LoadBalancer --port 80" % deployment, shell=True)
    p_object = subprocess.run(
        "kubectl get svc | grep %s | awk {'print $5'} | awk -F '[:/]' {'print $2'}" % deployment, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    port = p_object.stdout.decode("ascii")
    os.system("sleep 10")
    total_duration_m = total_duration // 60 + 1
    with open("%s/start_time" % version_folder, "w") as f:
        f.write(str(datetime.datetime.now()))
    os.system("tools/log_metrics.sh %s %s %s &" %
              (deployment, total_duration_m, version_folder))
    os.system("tools/log_vpa.sh %s %s %s &" %
              (vpa, total_duration_m, version_folder))

    reward = 0
    for i, (load, duration) in enumerate(zip(loads, per_load_duration)):
        p_object = subprocess.run("./wrk2/wrk -t%d -c%d -d%s -R%s http://localhost:%s" %
                                  (threads, clients, duration, load, port), stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        output = p_object.stdout.decode("ascii")
        with open(version_folder + "/wrk_%d.log" % i, "w") as f:
            f.write(output)
        m = re.search(r"(\d+) requests in", output)
        total_requests = 0
        if m:
            total_requests = float(m.group(1))
        reward += ((load - (total_requests/duration))/load) + 1.0 * half_life

        #reward += ((load - (total_requests/duration))/load) * duration

    #average_reward = reward/sum(per_load_duration)

    with open("%s/cost" % version_folder, "w") as f:
        f.write(str(reward))
    subprocess.run("kubectl delete svc %s" % deployment, shell=True)
    subprocess.run("kubectl delete -f %s" % vpa_file_path, shell=True)
    subprocess.run("kubectl delete -f %s" %
                   deployment_file_path, shell=True)
    write_n_vpa_evictions(version_folder)
    return reward

def write_n_vpa_evictions(version_folder):
    os.system(
        "kubectl get pods -n kube-system | grep updater | awk {'print $1'} | xargs kubectl logs -n kube-system | grep EvictedByVPA > %s/n_vpa_evictions" % version_folder)


def generate_workload(version_folder, experiment_version, total_duration,  experiment_type, workload_type, new_samples, half_life):
    reward = 1000000.
    if experiment_type == "nginx":
        reward = generate_workload_nginx(
            version_folder, experiment_version, total_duration, workload_type, new_samples, half_life)
    elif experiment_type == "sn":
        reward = generate_workload_sn(
            version_folder, experiment_version, total_duration, workload_type, new_samples, half_life)
    return reward


def get_reward(args, model_iteration, config, folder_suffix="", new_samples=True):
    """
    Common API for the optimization algorithms.
    Runs the experiment and returns the reward.
    """
    destination_folder = str(model_iteration)
    if folder_suffix:
        destination_folder += folder_suffix
    main_folder = os.path.join(
        args.experiment_folder, args.experiment_type + "-" + args.experiment_version)
    version_folder = os.path.join(main_folder, destination_folder)

    try:
        os.mkdir(main_folder)
    except FileExistsError:
        print("\t\n\nExperiment folder exists already. Do you want to skip (Press Ctrl+c)?\n\n Waiting for 1 minute.")

    try:
        os.mkdir(version_folder)
    except FileExistsError:
        print("\t\n\nExperiment folder exists already. Do you want to skip (Press Ctrl+c)?\n\n Waiting for 1 minute.")
        #os.system("sleep 60")
    os.system("cp configs/vpa_parameters.csv %s" % version_folder)
    df = pd.read_csv(version_folder+"/vpa_parameters.csv")

    with open("%s/config.txt" % version_folder, "w") as f:
        f.write(",".join(list(map(str, config))))
    vpa_deployment.deploy_vpa("localhost", config,)
    modify_deployment_file(version_folder,
                           args.experiment_version, args.experiment_type)
    reward = generate_workload(version_folder, args.experiment_version,
                               args.experiment_duration, args.experiment_type, args.workload_type, new_samples, config[0])
    return reward


def modify_deployment_file(version_folder, experiment_version, experiment_type):
    if experiment_type in ["nginx", "redis"]:
        modify_deployment_file_nginx(
            version_folder, experiment_version, experiment_type)


def modify_deployment_file_nginx(version_folder, version, experiment_type):
    # create a different vpa file.
    with open("examples/%s-vpa-template.yaml" % experiment_type) as vpa_f:
        data = yaml.safe_load(vpa_f)
    data['metadata']['name'] = "%s-vpa-%s" % (experiment_type, version)
    data['spec']['targetRef']['name'] = "%s-deployment-%s" % (
        experiment_type, version)
    with open(version_folder + "/%s-vpa-%s.yaml" % (experiment_type, version), "w") as vpa_f:
        yaml.dump(data, vpa_f)

    # create a different deployment file.
    with open("examples/%s-deployment-template.yaml" % experiment_type) as deployment_f:
        data = yaml.safe_load(deployment_f)
    data["metadata"]["name"] = "%s-deployment-%s" % (experiment_type, version)
    if experiment_type != "nginx":
        data["metadata"]["labels"]["app"] = "%s-deployment-%s" % (
            experiment_type, version)
    data["spec"]["selector"]["matchLabels"]["app"] = "%s-deployment-%s" % (
        experiment_type, version)
    data["spec"]["template"]["metadata"]["labels"]["app"] = "%s-deployment-%s" % (
        experiment_type, version)
    data["spec"]["template"]["spec"]["containers"][0]["name"] = "%s-container-%s" % (
        experiment_type, version)
    with open(version_folder + "/%s-deployment-%s.yaml" % (experiment_type, version), "w") as dep_f:
        yaml.dump(data, dep_f)


if __name__ == "__main__":
    args = arguments.argument_parser()
    get_reward(args, 0, [6, 0.15, 25], folder_suffix="", new_samples=True)
