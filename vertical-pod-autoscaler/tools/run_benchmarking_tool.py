import subprocess
import argparse




payload_size = 1000 # in bytes

command =  "redis-benchmark  -d 10 -l -t LPUSH -h 10.110.251.157  --csv"
for i in range(1,100):
  completed_process = subprocess.run(command, shell=True)
  print(completed_process)
