exp_folder=$1
kubectl apply -f examples/my-rec-vpa-random-2.yaml
kubectl apply  -f examples/my-rec-deployment-random-2.yaml
kubectl expose deployment my-rec-deployment-random-2 --type=LoadBalancer --port 80
port=`kubectl get svc | grep my-rec-deployment-random-2 | awk {'print $5'} | awk -F '[:/]' {'print $2'}`
sleep 600
total=400
sleep_interval=600
./log_vpa.sh my-rec-vpa-random-2 $total $exp_folder &
./log_metrics.sh my-rec-deployment-random-2 $total $exp_folder &
sleep 600
~/hey -z 30m -c 50 http://localhost:$port
sleep $sleep_interval
~/hey -z 50m -c 500 http://localhost:$port
sleep $sleep_interval
~/hey -z 50m -c 10 http://localhost:$port
sleep $sleep_interval
~/hey -z 30m -c 100 http://localhost:$port
sleep 3600
kubectl delete svc my-rec-deployment-random-2
kubectl delete -f examples/my-rec-vpa-random-2.yaml
kubectl delete -f examples/my-rec-deployment-random-2.yaml
