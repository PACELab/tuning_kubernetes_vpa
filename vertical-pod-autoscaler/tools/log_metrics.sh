
string=$1
DEFAULTDURATION=60
DEFAULTPATH="exp_logs"
total="${2:-$DEFAULTDURATION}"
folder="${3:-$DEFAULTPATH}"
namespace="${4:-default}"
mkdir -p $folder
date=$(date +%Y%m%d%H%M%S)
log_file="$folder/metrics-$string.log"

echo $log_file

i=1
while [ "$i" -le "$total" ]; do kubectl top pod -n $namespace | grep $string | awk {'print $2'} >> $log_file ;  i=$(( i + 1 ));sleep 30 ; done
