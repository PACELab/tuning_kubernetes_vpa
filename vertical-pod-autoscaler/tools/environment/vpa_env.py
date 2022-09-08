import random
import os
import sys
import subprocess

sys.path.append("/home/ubuntu/autoscaler/vertical-pod-autoscaler/tools")
import helper

def take_action(args, total_steps, action):
    experiment_version_folder = os.path.join(args.results_folder , args.experiment_type + "-" + args.experiment_version)
    return helper.get_reward(args, experiment_version_folder, total_steps, action)

def next_observation(args, model_iteration):
    """
    1) CPU and memory usage in % of each microservice in sequence
    2) CPU and memory usage in % of the node
    3) RPS
    4) Connections
    5) Request composition array in % (three values)
    """
    os.system("sleep 120") # sleep for the utilization files to be created.
    iteration_folder = str(model_iteration-1) # previous state
    experiment_version_folder = os.path.join(args.results_folder , args.experiment_type + "-" + args.experiment_version)
    destination_folder = os.path.join(experiment_version_folder, iteration_folder)
    observation = []
    #observation += random.sample(range(0, 100), 1 * 2)
    node_total_memory = 8000 # in megabytes
    node_total_cpu = 8000 # in millicores
    print("out")
    try:
        print(subprocess.run("cat %s/pod_*.csv | awk -F',' '{print $3}' | tail +2 | datamash max 1"%destination_folder, stdout=subprocess.PIPE, shell=True).stdout.decode("ascii").strip())
        cpu_nginx  = (float(subprocess.run("cat %s/pod_*.csv | awk -F',' '{print $3}' | tail +2 | datamash max 1"%destination_folder, stdout=subprocess.PIPE, shell=True).stdout.decode("ascii").strip())/node_total_cpu) * 100
        mem_nginx = (float(subprocess.run( "cat %s/pod_*.csv | awk -F',' '{print $3}' | tail +2 | datamash max 1"%destination_folder, stdout=subprocess.PIPE, shell=True).stdout.decode("ascii").strip())/node_total_memory) * 100
        observation += [cpu_nginx, mem_nginx]
        cpu_node  = (float(subprocess.run( "cat %s/node_userv3-m2-node.csv | awk -F',' '{print $3}' | tail +2 | datamash max 1"%destination_folder, stdout=subprocess.PIPE, shell=True).stdout.decode("ascii").strip()) / node_total_cpu) * 100
        mem_node = (float(subprocess.run( "cat %s/node_userv3-m2-node.csv | awk -F',' '{print $4}' | tail +2 | datamash max 1"%destination_folder, stdout=subprocess.PIPE, shell=True).stdout.decode("ascii").strip())/node_total_memory) * 100
        observation += [cpu_node, mem_node]
        observation += [10000] #rps
        observation += [100] #connections
        observation += [100] #request composition
    except:
        observation =   [0, 0, 0, 0, 0, 0, 0]
    print(observation)
    return observation