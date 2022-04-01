string=$1
DEFAULTDURATION=60
DEFAULTPATH="exp_logs"
total="${2:-$DEFAULTDURATION}"
folder="exp_logs/${3:-$DEFAULTPAT}"
mkdir -p $folder
date=$(date +%Y%m%d%H%M%S)
log_file="$folder/metrics-$string-$date.log"

echo $log_file

for (( i=1; i <= $total; ++i )); do kubectl top pod | grep $string | awk {'print $2'} >> $log_file ; sleep 60 ; done
