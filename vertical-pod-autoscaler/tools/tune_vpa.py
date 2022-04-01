import sys
import os
import re
import subprocess
from kubernetes import client, config, utils


def load_kube_config():
    config.load_kube_config()

def email_error():
    pass


def deploy_vpa(control_plane):
    ns = "kube-system"
    metrics_server_manifest = '../metrics_server/deployment.yaml'

    load_kube_config()
    k8s_client = client.ApiClient()
    api_instance = client.CoreV1Api(k8s_client)


    metrics_server = api_instance.list_namespaced_pod(ns, label_selector="k8s-app=metrics-server")
    if len(metrics_server.items) > 0:
        os.system("kubectl delete -f %s"%metrics_server_manifest)

        #TODO: the pod is deleted but Kubernetes brings up another service before the new one is created. Figure out.`
        #api_instance.delete_namespaced_pod(metrics_server.items[0].metadata.name, ns)

    utils.create_from_yaml(k8s_client, metrics_server_manifest, verbose=True)

    bring_down_vpa = "./hack/vpa-down.sh"
    subprocess.run(bring_down_vpa, shell=True)
    bring_up_vpa = "./hack/vpa-up.sh"
    subprocess.run(bring_up_vpa, shell=True)

    vpa_system_pods = ["recommender", "updater", "admission-controller"]
    for pod in vpa_system_pods:
        log = api_instance.read_namespaced_pod_log(name=pod_name, namespace=ns)
        if re.search(log, '^E[0-9]{4}'):
            print("Error in %s logs")
            sys.exit()
            #TODO: send email

deploy_vpa("")

