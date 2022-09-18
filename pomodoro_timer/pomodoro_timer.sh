#!/bin/bash

sig_int_handle()
{
        sig_int_triggerd=1
}


interruptible_sleep()
{
	seconds=$1
	while true; do
		if [ "$sig_int_triggerd" = "1" ]; then
			break
		fi
		sleep 1;
		seconds=$((seconds - 1));
		if [ $seconds -eq 0 ]; then
			break
		fi
	done
}

sig_int_triggerd=0
trap sig_int_handle SIGINT
MSG="$1"
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
paplay /usr/share/sounds/freedesktop/stereo/complete.oga
date
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
	date
fi


