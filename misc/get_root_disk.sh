#!/bin/bash
# Get the root disk in current Linux system
# Usage: $0

cd /
# df with directory ("." for example) will only display filesystem information
# belongs to such directory.
echo "df -h for root directory"
df -h .
lvm=`df -h . | tail -f -n1 | cut -d \  -f 1`
echo "lvm is $lvm"

lvm=`basename $lvm`
echo "possible root disk are:"
lsblk |grep "\($lvm\)" -B 1

echo "disk string:"
disk_desc=`lsblk |grep "\(disk\)\|\($lvm\)" -B 1 | head -n2 |tail -n1 | sed "s/\ \ */ /g"`
echo "Only choose the first one currently:"
root_disk=`echo $disk_desc | cut -d \  -f 1`
root_disk_size=`echo $disk_desc | cut -d \  -f 4`
echo "root disk<${root_disk}>, size<$root_disk_size}"
