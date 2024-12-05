#!/usr/bin/bash
for n in {1..5}
do
    nohup python3 logging_cabinet_$n.py > cabinet_$n.out 2>&1 &
done
nohup python3 logging_cabinet_test.py > cabinet_test.out 2>&1 &
nohup python3 logging_cabinet_test1_udp.py > cabinet_test1_udp.out 2>&1 &
nohup python3 logging_cabinet_6007.py > logging_cabinet_6007.out 2>&1 &
nohup python3 logging_cabinet_6008.py > logging_cabinet_6008.out 2>&1 &
nohup python3 logging_cabinet_6009.py > logging_cabinet_6009.out 2>&1 &
nohup python3 logging_cabinet_6010.py > logging_cabinet_6010.out 2>&1 &
echo "Create server succesfully"
