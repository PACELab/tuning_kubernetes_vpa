exp_folder=$1
kubectl apply -f examples/my-rec-vpa.yaml
kubectl apply  -f examples/my-rec-deployment.yaml 
kubectl expose deployment my-rec-deployment --type=LoadBalancer --port 80
port=`kubectl get svc | grep my-rec-deployment | awk {'print $5'} | awk -F '[:/]' {'print $2'}`
sleep 600
total=200
sleep_interval=120
./log_vpa.sh my-rec-vpa $total $exp_folder &
./log_metrics.sh my-rec-deployment $total $exp_folder &
~/hey -z 30m -c 50 http://localhost:$port
sleep $sleep_interval
~/hey -z 50m -c 50 http://localhost:$port
sleep $sleep_interval 
~/hey -z 50m -c 50 http://localhost:$port
sleep $sleep_interval 
~/hey -z 30m -c 50 http://localhost:$port
sleep 1200
kubectl delete svc my-rec-deployment
kubectl delete -f examples/my-rec-vpa.yaml
kubectl delete -f examples/my-rec-deployment.yaml 
