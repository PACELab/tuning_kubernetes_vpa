import re
import sys
import yaml
import os
import subprocess

import pandas as pd
import numpy as np

import vpa_deployment
import arguments

loads = []
per_load_duration = []


def get_init_points_default():
    return ([24, 24, 24, 8], 100)


def generate_workload_nginx(version_folder, experiment_version, total_duration, workload_type, new_samples, n_load_changes=4):
    global loads
    global per_load_duration
    threads = 2
    clients = 100
    total_duration = int(total_duration)

    if new_samples:
        if workload_type == "diurnal":
            #loads = np.random.normal(2000, 200, n_load_changes)
            loads = [9985, 10145,  9894 , 10127]
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
            loads = [9985, 10145,  9894 , 10127]
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
    print("tools/log_metrics.sh %s %s %s &" %
          (deployment, total_duration, version_folder))
    os.system("tools/log_metrics.sh %s %s %s &" %
              (deployment, total_duration, version_folder))
    os.system("tools/log_vpa.sh %s %s %s &" %
              (vpa, total_duration, version_folder))

    reward = 0
    for i, (load, duration) in enumerate(zip(loads, per_load_duration)):
        p_object = subprocess.run("./wrk2/wrk -t%d -c%d -d%s -R%s http://localhost:%s" %
                                  (threads, clients, duration, load, port), stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        output = p_object.stdout.decode("ascii")
        with open(version_folder + "/wrk_%d.log" % i, "w") as f:
            f.write(output)
        m = re.match(r"(\d+) requests in", p_object.stdout.decode("ascii"))
        total_requests = 0
        if m:
            total_requests = m.group(1)
        reward += ((load - (total_requests/duration))/load) * duration
    
    average_reward = reward/sum(per_load_duration)

    #subprocess.run("kubectl delete svc %s" % deployment, shell=True)
    #subprocess.run("kubectl delete -f %s" % vpa_file_path, shell=True)
    #subprocess.run("kubectl delete -f %s" %
    #               deployment_file_path, shell=True)

    return average_reward


def generate_workload(version_folder, experiment_version, total_duration,  experiment_type, workload_type, new_samples,):
    reward = 1000000.
    if experiment_type == "nginx":
        reward = generate_workload_nginx(
            version_folder, experiment_version, total_duration, workload_type, new_samples,)
    return reward


def get_reward(args, model_iteration, config, new_samples=True):
    """
    Common API for the optimization algorithms.
    Runs the experiment and returns the reward.
    """
    version_folder = os.path.join(args.experiment_folder,
                                  args.experiment_type + "-" + args.experiment_version)
    try:
        os.mkdir(version_folder)
    except FileExistsError:
        print("\t\n\nExperiment folder exists already. Do you want to skip (Press Ctrl+c)?\n\n Waiting for 1 minute.")
        #os.system("sleep 60")
    os.system("cp configs/vpa_parameters.csv %s" % version_folder)
    df = pd.read_csv(version_folder+"/vpa_parameters.csv")

    vpa_deployment.deploy_vpa("localhost", config,)
    modify_deployment_file(version_folder,
                           args.experiment_version, args.experiment_type)
    reward = generate_workload(version_folder, args.experiment_version,
                               args.experiment_duration, args.experiment_type, args.workload_type, new_samples)
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


"""
def modify_deployment_file_redis(experiment_folder, version):
  # create a different vpa file.
  with open("examples/redis-vpa-template.yaml") as redis_vpa_f:
    data = yaml.load(redis_vpa_f)
  data['metadata']['name'] = "redis-vpa-%d"%version
  data['spec']['targetRef']['name'] = "redis-master-%d"%version
  with open(experiment_folder + "/redis-vpa-%d.yaml"%version,"w") as redis_vpa_f:
    yaml.dump(data, redis_vpa_f) 

  # create a different deployment file.
  with open(experiment_folder + "/redis-deployment-template.yaml") as redis_deployment_f:
    data = yaml.load(redis_deployment_f)
  data["metadata"]["name"] = "redis-master-%d"%version
  data["metadata"]["labels"]["app"] = "redis-%d"%version
  data["spec"]["selector"]["matchLabels"]["app"] = "redis-%d"%version
  data["spec"]["template"]["metadata"]["labels"]["app"] = "redis-%d"%version
  data["spec"]["template"]["spec"]["containers"][0]["name"] = "master-%d"%version
  with open(experiment_folder + "/redis-deployment-%d.yaml"%version,"w") as redis_dep_f:
    yaml.dump(data, redis_dep_f) 
  """

if __name__ == "__main__":
    args = arguments.argument_parser()
    get_reward(args, 0, [24, 24, 24, 8], new_samples=True)
