#!/bin/bash
KILL_SIG_FILE=/tmp/kill_eagle

if [ -f $KILL_SIG_FILE ]; then
    echo "[ERROR] Kill signal $KILL_SIG_FILE detected"
    exit 127
fi

echo "Kicked off iostat & vmstat"
pids=$(ps aux | grep '[O]penSearch' | awk '{print $2}')
OS_PID=$(echo "$pids" | sed -n '2p')
echo "Detected OS PID as : $OS_PID"
mkdir /home/ec2-user/jstack-outputs

LastOutputMin=-1

while [ ! -f $KILL_SIG_FILE ]; do 
    currMin=$(date +%m-%dT%H-%M)
    if [[ $currMin != $LastOutputMin ]]; then
        nohup date +%m-%dT%H-%M-%S >> /home/ec2-user/iostat.out &
        nohup iostat >> /home/ec2-user/iostat.out &
        nohup date +%m-%dT%H-%M-%S >> /home/ec2-user/vmstat.out &
        nohup vmstat >> /home/ec2-user/vmstat.out &
        LastOutputMin=$currMin
        echo "Last iostat and vmstat output minute is: ${LastOutputMin}"
    fi

    currTS=$(date +%m-%dT%H-%M-%S)
    currMinTS=$(echo $currTS | cut -f1-3 -d'-')
    outputFile=/home/ec2-user/jstack-outputs/jstack-${currTS}.out
    jstack $OS_PID > $outputFile    
    # sleep 1 minute
    sleep 60
    # check for zipping last 1 min
    nextMinTS=$(date +%m-%dT%H-%M)
    if [[ $nextMinTS != $currMinTS ]]; then
        tar -czf /home/ec2-user/jstack-${currMinTS}.tgz /home/ec2-user/jstack-${currMinTS}*.out
        rm -rf /home/ec2-user/jstack-${currMinTS}*.out
    fi
done


echo "[WARN] Kill signal $KILL_SIG_FILE detected at "$(date)
echo "Killing ALL iostat "
echo "Current list:"
ps -ef | grep -w iostat
set -x
killall iostat
echo "Killing ALL vmstat "
echo "Current list:"
ps -ef | grep -w vmstat
set -x
killall vmstat
set +x
echo "Post Kill list:"
ps -ef | grep -w iostat
ps -ef | grep -w vmstat