#!/bin/bash

sig_int_handle()
{
        sig_int_triggerd=1
}


interruptible_sleep()
{
	unit=0.2
	scale=10
	secondsxastep=2 # 0.2 * 10
	seconds=$1
	secondsxa=$((seconds * scale))
	while true; do
		if [ "$sig_int_triggerd" = "1" ]; then
			break
		fi
		sleep $unit;
		secondsxa=$((secondsxa - $secondsxastep));
		if [ $secondsxa -eq 0 ]; then
			break
		fi
	done
}

sig_int_triggerd=0
trap sig_int_handle SIGINT

MSG="$1"
echo $MSG
TIME_REMAIN_UNIT=300
date
for i in `seq 0 4`; do
	echo -n -e "\r$((25 - $i * 5)) min left"
	interruptible_sleep $TIME_REMAIN_UNIT
	if [ "$sig_int_triggerd" = "1" ]; then
		break
	fi
done
notify-send "$MSG"
paplay /usr/share/sounds/freedesktop/stereo/complete.oga &
if [ "$sig_int_triggerd" = "1" ]; then
	echo -n -e "\r"
	date
fi
if [ "$sig_int_triggerd" = "0" ]; then
	i=0
	while true; do
		echo -n -e "\r$(($i * 5)) min elapsed"
		i=$((i+1))
		interruptible_sleep $TIME_REMAIN_UNIT
		if [ "$sig_int_triggerd" = "1" ]; then
			break
		fi
	done
	echo -n -e "\r"
	notify-send "$MSG"
	paplay /usr/share/sounds/freedesktop/stereo/complete.oga &
	date
fi
