#!/usr/bin/bash
for n in {6..13}
do
    nohup python3 logging_envisor_testing_$n.py > envisor_testing_$n.out 2>&1 &
done
