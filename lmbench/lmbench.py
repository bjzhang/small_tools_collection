#!/usr/bin/env python

from __future__ import print_function
import paramiko
import time

def ssh_cmd(host, user, cmd, slient=True):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, username=user, timeout=120)
	stdin,stdout,stderr = ssh.exec_command(cmd)
	if not slient:
		print("stdout: " + str(stdout.readlines()))
		print("stderr: " + str(stderr.readlines()))

def ssh_wait_connection(host, normal_user):
	while True:
		try:
			ssh_cmd(host, normal_user, "echo -n")
			break
		except:
			print(".", end="")
			time.sleep(10)

host="D03-02"
normal_user="z00293696"
root_user="root"

print("Current machine")
ssh_cmd(host, normal_user, "uname -a", False)
ssh_cmd(host, normal_user, "zgrep ILP32 /proc/config.gz", False)

print("Changing grub.cfg")
ssh_cmd(host, normal_user, "grep z00293696 /boot/EFI/grub2/grub.cfg", False)
ssh_cmd(host, root_user, 'sed -i "s/^set.default.*$/set default=z00293696-upstream/g" /boot/EFI/grub2/grub.cfg', False)
print("Result")
ssh_cmd(host, normal_user, "grep z00293696 /boot/EFI/grub2/grub.cfg", False)


print("Rebooting")
ssh_cmd(host, root_user, "reboot", False)

print("Waiting for reboot: ", end="")
ssh_wait_connection(host, normal_user)
print("done")

count = 0
while(count < 10):
	print("count is " + str(count))
	ssh_cmd(host, normal_user, "cd /home/z00293696/works/source/testsuite/lmbench/lmbench-3.0-a9; make rerun", False)
	count = count + 1

#print("Changing grub.cfg")
#ssh_cmd(host, normal_user, "grep z00293696 /boot/EFI/grub2/grub.cfg", False)
#ssh_cmd(host, root_user, 'sed -i "s/^set.default.*$/set default=z00293696-upstream-ilp32-disabled/g" /boot/EFI/grub2/grub.cfg', False)
#print("result")
#ssh_cmd(host, normal_user, "grep z00293696 /boot/EFI/grub2/grub.cfg", False)

