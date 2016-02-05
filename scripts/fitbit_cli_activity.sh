#!/bin/bash

Q_ITEMS="heart calories caloriesBMR steps distance floors elevation minutesSedentary minutesLightlyActive minutesFairlyActive minutesVeryActive activityCalories"
SUID="f810aa90-d7a0-44a6-95aa-7d7a35c91161"
API_SERVER="http://kchien.myqnapcloud.com:8888/v1"

echo "$0 start"
for (( c=10; ; c++ ))
do
    #base_date="2015-08-$c"
    base_date=`date +"%4Y-%2m-%2d"`
    for item in $Q_ITEMS
        do
            time curl -L ${API_SERVER}/user/${SUID}/fitbit/activities/${item}/date/$base_date/1d
        done

    echo "Fitbit Activity #" $c
    sleep 500
done
echo "$0 Done"
