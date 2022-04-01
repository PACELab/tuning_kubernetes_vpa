import yaml
import sys

version = int(sys.argv[1])

with open("examples/redis-vpa-template.yaml") as redis_vpa_f:
  data = yaml.load(redis_vpa_f)
data['metadata']['name'] = "redis-vpa-%d"%version
data['spec']['targetRef']['name'] = "redis-master-%d"%version

with open("examples/redis-vpa-%d.yaml"%version,"w") as redis_vpa_f:
  yaml.dump(data, redis_vpa_f) 

with open("examples/redis-deployment-template.yaml") as redis_deployment_f:
  data = yaml.load(redis_deployment_f)

data["metadata"]["name"] = "redis-master-%d"%version
data["metadata"]["labels"]["app"] = "redis-%d"%version
data["spec"]["selector"]["matchLabels"]["app"] = "redis-%d"%version
data["spec"]["template"]["metadata"]["labels"]["app"] = "redis-%d"%version
data["spec"]["template"]["spec"]["containers"][0]["name"] = "master-%d"%version


with open("examples/redis-deployment-%d.yaml"%version,"w") as redis_dep_f:
  yaml.dump(data, redis_dep_f) 
