exp_folder=$1
exp_type=$2
exp_number=$3
kubectl apply -f examples/my-rec-vpa-random-$2.yaml
kubectl apply  -f examples/my-rec-deployment-random-35.yaml
kubectl expose deployment my-rec-deployment-random-35 --type=LoadBalancer --port 80
port=`kubectl get svc | grep my-rec-deployment-random-35 | awk {'print $5'} | awk -F '[:/]' {'print $2'}`
sleep 600
total=140
./log_vpa.sh my-rec-vpa-random-35 $total $exp_folder &
./log_metrics.sh my-rec-deployment-random-35 $total $exp_folder &
sleep 2700
./wrk2/wrk -t2 -c100 -d5m -R3699 http://localhost:$port >> ./exp_logs/$exp_folder/wrk2.log
sleep 2700
./wrk2/wrk -t2 -c100 -d5m -R4163 http://localhost:$port >> ./exp_logs/$exp_folder/wrk2.log
sleep 1200
kubectl delete svc my-rec-deployment-random-35
kubectl delete -f examples/my-rec-vpa-random-35.yaml
kubectl delete -f examples/my-rec-deployment-random-35.yaml
