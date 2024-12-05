#!usr/bin/bash
file_to_copy="logging_cabinet_1.py"  # Replace this with the name of the file you want to copy

for i in {2..5}
do
    new_name=$(printf "logging_cabinet_%d.py" $i)  # This will create names like copy_001.txt, copy_002.txt, etc.
    cp $file_to_copy $new_name
done
