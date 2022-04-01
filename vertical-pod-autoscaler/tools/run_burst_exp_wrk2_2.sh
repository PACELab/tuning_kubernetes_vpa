exp_folder=$1
kubectl apply -f examples/my-rec-vpa-random-37.yaml
kubectl apply  -f examples/my-rec-deployment-random-37.yaml
kubectl expose deployment my-rec-deployment-random-37 --type=LoadBalancer --port 80
port=`kubectl get svc | grep my-rec-deployment-random-37 | awk {'print $5'} | awk -F '[:/]' {'print $2'}`
sleep 600
total=140
./log_vpa.sh my-rec-vpa-random-37 $total $exp_folder &
./log_metrics.sh my-rec-deployment-random-37 $total $exp_folder &
sleep 2700
./wrk2/wrk -t2 -c100 -d5m -R4139 http://localhost:$port >> ./exp_logs/$exp_folder/wrk2.log
sleep 2700
./wrk2/wrk -t2 -c100 -d5m -R3636 http://localhost:$port >> ./exp_logs/$exp_folder/wrk2.log
sleep 1200
kubectl delete svc my-rec-deployment-random-37
kubectl delete -f examples/my-rec-vpa-random-37.yaml
kubectl delete -f examples/my-rec-deployment-random-37.yaml
