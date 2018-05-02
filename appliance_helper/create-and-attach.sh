#!/bin/bash

# start over
# sudo virsh detach-disk ceph-8.02-bcache-01  vdb
# sudo virsh detach-disk ceph-8.02-bcache-01  vda
# sudo virsh vol-delete ceph-8.02-bcache-01-extend-disk.raw --pool zhangjian
# sudo virsh vol-delete ceph-8.02-bcache-01-ceph-disk.raw --pool zhangjian

set -e

DISK_PREFIX=ceph-8.02-bcache
DOMAIN_PREFIX=ceph-8.02-bcache
COUNT=3
if [ $COUNT -gt 9 ]; then
	echo do not support more than 10. exit
	exit
fi
for i in `seq $COUNT`; do
	sudo virsh vol-create-as zhangjian $DISK_PREFIX-0$i-extend-disk.raw --capacity 5g
	sudo virsh vol-create-as zhangjian $DISK_PREFIX-0$i-ceph-disk.raw --capacity 10g
	sudo virsh attach-disk $DOMAIN_PREFIX-0$i /mnt/images/zhangjian/$DISK_PREFIX-0$i-extend-disk.raw vda --current
	sudo virsh attach-disk $DOMAIN_PREFIX-0$i /mnt/images/zhangjian/$DISK_PREFIX-0$i-ceph-disk.raw vdb --current
done

