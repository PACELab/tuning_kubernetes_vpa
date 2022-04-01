exp_folder=$1
kubectl apply -f examples/my-rec-vpa_copy.yaml
kubectl apply  -f examples/my-rec-deployment_copy.yaml
kubectl expose deployment my-rec-deployment-copy --type=LoadBalancer --port 80
port=`kubectl get svc | grep my-rec-deployment-copy | awk {'print $5'} | awk -F '[:/]' {'print $2'}`
sleep 600
total=300
sleep_interval=3600
./log_vpa.sh my-rec-vpa-copy $total $exp_folder &
./log_metrics.sh my-rec-deployment-copy $total $exp_folder &
sleep 600
~/hey -z 10m -c 100 http://localhost:$port
sleep $sleep_interval
~/hey -z 10m -c 100 http://localhost:$port
sleep $sleep_interval
~/hey -z 10m -c 100 http://localhost:$port
sleep $sleep_interval
~/hey -z 20m -c 100 http://localhost:$port
sleep 600
kubectl delete svc my-rec-deployment-copy
kubectl delete -f examples/my-rec-vpa_copy.yaml
kubectl delete -f examples/my-rec-deployment_copy.yaml
