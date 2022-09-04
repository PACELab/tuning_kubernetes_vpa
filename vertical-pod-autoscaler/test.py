from kubernetes import client, config, utils
def load_kube_config():
    config.load_kube_config()
load_kube_config()
ns="kube-system"
k8s_client = client.ApiClient()
api_instance = client.CoreV1Api(k8s_client)       

pod="recommender"
pod_list = api_instance.list_namespaced_pod(
            ns, label_selector="app=vpa-%s" % pod)
print(pod_list)
log = api_instance.read_namespaced_pod_log(
            name=pod_list.items[0].metadata.name, namespace=ns)
print(log)
