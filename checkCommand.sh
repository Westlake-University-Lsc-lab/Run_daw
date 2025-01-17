#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <command_to_check>"
    exit 1
fi

COMMAND_TO_CHECK=$1
USER_TO_CHECK="daq"

ps aux | grep "$COMMAND_TO_CHECK" > tmp.csv

if [ -s tmp.csv ]; then
    awk '{
        split($0, a, " "); 
        print $1, $2, $3 "%", $4 "%", $5, $6, $7, $8, $9, $NF; 
    }' tmp.csv | while read -r user pid cpu mem vsz rss tty stat start_time command; do
        if [[ $user == "$USER_TO_CHECK" ]]; then  
            echo "User: $user, process $command, status: $stat"
        fi
    done > processed_output.csv 
else
    echo "Do not find$COMMAND_TO_CHECK process running."
fi

rm  tmp.csv