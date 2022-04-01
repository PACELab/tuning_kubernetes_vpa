vpa_resource=$1
DEFAULTDURATION=60
DEFAULTPATH="exp_logs"

total="${2:-$DEFAULTDURATION}"
folder="exp_logs/${3:-$DEFAULTPAT}"
mkdir -p $folder
date=$(date +%Y%m%d%H%M%S)
log_file="$folder/mem-$vpa_resource-$date.log"

echo $log_file

for (( i=1; i <= $total; ++i )); do kubectl describe vpa $vpa_resource | egrep -A 2 "  Target:" | grep Memory | awk {'print $2'} >> $log_file; sleep 60 ; done; 

