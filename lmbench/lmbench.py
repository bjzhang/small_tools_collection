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

def run_benchmark(host, normal_user, root_user, grubentry, total_count, test_user, testcmd):
	print(host)
	print(normal_user)
	print(grubentry)
	print(total_count)
	print(test_user)
	print(testcmd)

	print("Changing grub.cfg")
	ssh_cmd(host, root_user, 'sed -i "s/^set.default.*$/set default=' + grubentry + '/g" /boot/EFI/grub2/grub.cfg', False)
	print("result")
	ssh_cmd(host, normal_user, "grep z00293696 /boot/EFI/grub2/grub.cfg", False)

	print("Rebooting")
	ssh_cmd(host, root_user, "reboot", False)

	print("Waiting for reboot: ", end="")
	ssh_wait_connection(host, normal_user)
	print("done")

	print("Current machine")
	ssh_cmd(host, normal_user, "uname -a", False)
	ssh_cmd(host, normal_user, "zgrep ILP32 /proc/config.gz", False)

	count = 0
	while(count < total_count):
		print("count is " + str(count))
		ssh_cmd(host, test_user, testcmd, False)
		count = count + 1

run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry="z00293696-upstream", total_count=5, test_user="z00293696", testcmd="cd /home/z00293696/works/source/testsuite/lmbench/lmbench-3.0-a9; make rerun")

run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry="z00293696-upstream-ilp32-disabled", total_count=5, test_user="z00293696", testcmd="cd /home/z00293696/works/source/testsuite/lmbench/lmbench-3.0-a9; make rerun")

run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry="z00293696-upstream", total_count=1, test_user="root", testcmd="cd /home/z00293696/speccpu2006;. ./shrc; runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=ref --noreportable --tune=base --iterations=1 perlbench bzip2 gcc mcf gobmk hmmer sjeng libquantum h264ref omnetpp astar xalancbmk")

run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry="z00293696-upstream-ilp32-disabled", total_count=1, test_user="root", testcmd="cd /home/z00293696/speccpu2006;. ./shrc; runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=ref --noreportable --tune=base --iterations=1 perlbench bzip2 gcc mcf gobmk hmmer sjeng libquantum h264ref omnetpp astar xalancbmk")
total_count=10


