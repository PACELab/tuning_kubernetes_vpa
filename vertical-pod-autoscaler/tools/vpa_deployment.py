import sys
import os
import re
import subprocess

import yaml
import pandas as pd
from kubernetes import client, config, utils


def load_kube_config():
    config.load_kube_config()


def email_error():
    pass


def convert_to_hms(value):
    hour = int(value)
    minutes = value % 1 * 100
    minutes = int(minutes)
    return "%sh%sm" % (hour, minutes)


def update_config(config):
    parameter_meta_df = pd.read_csv("configs/vpa_parameters.csv")
    parameters = parameter_meta_df["parameter"].tolist()
    home = os.path.expanduser("~")
    recommender_deployment_default = home + \
        "/autoscaler/vertical-pod-autoscaler/tools/deploy/recommender-deployment.yaml"
    updated_recommender_deployment = home + \
        "/autoscaler/vertical-pod-autoscaler/deploy/recommender-deployment.yaml"

    with open(recommender_deployment_default) as f:
        data = f.read()
    # file has two yaml documents.
    yaml_docs = list(yaml.load_all(data, Loader=yaml.loader.SafeLoader))

    for doc in yaml_docs:
        # the deployment document has to be updated.
        if doc["kind"] == "Deployment":
            # get recommender container.
            recommender_container = doc["spec"]["template"]["spec"]["containers"][0]
            # pass args to recommender container.
            if "args" not in recommender_container:
                recommender_container["args"] = []
            for index, value in enumerate(config):
                if index == 0:
                    hms_value = convert_to_hms(value)
                    recommender_container["args"].append(
                        "--%s=%s" % (parameters[index], hms_value))
                else:
                    recommender_container["args"].append(
                        "--%s=%s" % (parameters[index], value))
    with open(updated_recommender_deployment, "w") as f:
        yaml.dump_all(list(yaml_docs), f)


def deploy_vpa(control_plane, config, clean_setup=True):
    ns = "kube-system"
    metrics_server_manifest = 'metrics_server/deployment.yaml'

    # load kube config and create clients
    load_kube_config()
    k8s_client = client.ApiClient()
    api_instance = client.CoreV1Api(k8s_client)

    if clean_setup:
        # if metric server is deployed, delete it.
        metrics_server = api_instance.list_namespaced_pod(
            ns, label_selector="k8s-app=metrics-server")
        if len(metrics_server.items) > 0:
            os.system("kubectl delete -f %s" % metrics_server_manifest)

            # TODO: the pod is deleted but Kubernetes brings up another service before the new one is created. Figure out.`
            #api_instance.delete_namespaced_pod(metrics_server.items[0].metadata.name, ns)

        # create a new metric server.
        utils.create_from_yaml(
            k8s_client, metrics_server_manifest, verbose=True)

        bring_down_vpa = "./hack/vpa-down.sh"
        subprocess.run(bring_down_vpa, shell=True)

    if len(config) > 0:
        update_config(config)

    if clean_setup:
        bring_up_vpa = "./hack/vpa-up.sh"
        subprocess.run(bring_up_vpa, shell=True)
    else:
        # TODO: make this generic. get a list of touched files from update_config
        os.system("kubectl apply -f  ../deploy/recommender_deployment.yam")

    # TODO: wait till the states of all the containers change to running.
    os.system("sleep 30")
    # check if VPA deployment was successful.
    vpa_system_pods = ["recommender", "updater", "admission-controller"]
    for pod in vpa_system_pods:
        pod_list = api_instance.list_namespaced_pod(
            ns, label_selector="app=vpa-%s" % pod)
        log = api_instance.read_namespaced_pod_log(
            name=pod_list.items[0].metadata.name, namespace=ns)
        if re.search(r'^E[0-9]{4}', log):
            print("Error in %s logs")
            sys.exit()
            # TODO: send email
