import yaml
import sys


def modify_deployment_file(experiment_folder, experiment_version, experiment_type):
    if experiment_type in ["nginx", "redis"]:
        modify_deployment_file_nginx(
            experiment_folder, experiment_version, experiment_type)


def modify_deployment_file_nginx(experiment_folder, version, experiment_type):
    # create a different vpa file.
    with open("examples/%s-vpa-template.yaml" % experiment_type) as vpa_f:
        data = yaml.load(vpa_f)
    data['metadata']['name'] = "%s-vpa-%d" % (experiment_type, version)
    data['spec']['targetRef']['name'] = "%s-master-%d" % (
        experiment_type, version)
    with open(experiment_folder + "/%s-vpa-%d.yaml" % (experiment_type, version), "w") as vpa_f:
        yaml.dump(data, vpa_f)

    # create a different deployment file.
    with open(experiment_folder + "/%s-deployment-template.yaml" % experiment_type) as deployment_f:
        data = yaml.load(deployment_f)
    data["metadata"]["name"] = "%s-master-%d" % (experiment_type, version)
    data["metadata"]["labels"]["app"] = "%s-%d" % (experiment_type, version)
    data["spec"]["selector"]["matchLabels"]["app"] = "%s-%d" % (
        experiment_type, version)
    data["spec"]["template"]["metadata"]["labels"]["app"] = "%s-%d" % (
        experiment_type, version)
    data["spec"]["template"]["spec"]["containers"][0]["name"] = "%s-master-%d" % (
        experiment_type, version)
    with open(experiment_folder + "/%s-deployment-%d.yaml" % (experiment_type, version), "w") as dep_f:
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
