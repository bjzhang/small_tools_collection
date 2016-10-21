#!/usr/bin/env python
from __future__ import print_function
import paramiko
import time
import logging
import select
import datetime

def ssh_cmd(host, user, cmd, slient=True):
#	print("Testing on " + host + " with user: " + user + " cmd: <" + cmd + ">")
#	logging.getLogger("paramiko").setLevel(logging.WARNING) ssh = paramiko.SSHClient()
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, username=user, timeout=120)
	for i, c in enumerate(cmd):
		print(c)
		stdin,stdout,stderr = ssh.exec_command(c)
		if not slient:
			print("stdout: " + str(stdout.readlines()))
			print("stderr: " + str(stderr.readlines()))

def ssh_wait_connection(host, normal_user):
	while True:
		try:
			ssh_cmd(host, normal_user, ["echo -n"])
			break
		except:
			print(".", end="")
			time.sleep(10)

def ssh_transport(host, user, cmd):
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, username=user, timeout=120)
	transport = ssh.get_transport()
	for i, c in enumerate(cmd):
		print(c)
		channel = transport.open_session()
		channel.exec_command(c)
		while True:
			r, w, x = select.select([channel], [], [], 0.0)
			if len(r) > 0:
				s = channel.recv(1024)
				if len(s) > 0:
					print(s, end="")
				else:
					break

def run_benchmark(host, normal_user, root_user, grubentry, total_count, test_user, testcmd, reboot=True):
	print(host)
	print(normal_user)
	print(grubentry)
	print(total_count)
	print(test_user)
	dt = datetime.datetime.now()
	print(str(dt))
	for i, el in enumerate(testcmd):
		print(el)

	ssh_wait_connection(host, normal_user)
	if reboot:
		print("Changing grub.cfg")
		ssh_cmd(host, root_user, ['sed -i "s/^set.default.*$/set default=' + grubentry + '/g" /boot/EFI/grub2/grub.cfg'], False)
		print("result")
		ssh_cmd(host, normal_user, ["grep z00293696 /boot/EFI/grub2/grub.cfg"], False)

		print("Rebooting")
		ssh_cmd(host, root_user, ["reboot"], False)

		print("Waiting for reboot: ", end="")
		ssh_wait_connection(host, normal_user)
		print("done")

	print("Current machine")
	ssh_cmd(host, normal_user, ["uname -a"], False)
	ssh_cmd(host, normal_user, ["zgrep ILP32 /proc/config.gz"], False)

	count = 0
	while(count < total_count):
		print("count is " + str(count))
		ssh_transport(host, test_user, testcmd)
		count = count + 1

no_ilp32="z00293696-upstream-no-aarch32"
ilp32_disabled="z00293696-upstream-ilp32-disabled-no-aarch32"

round_max = 6
round_cur = 0

while (round_cur < round_max):
	print("round: " + str(round_cur))
	run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry=no_ilp32, total_count=5, test_user="z00293696", testcmd=["cd /home/z00293696/works/source/testsuite/lmbench/lmbench-3.0-a9; make rerun"])
	run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry=ilp32_disabled, total_count=5, test_user="z00293696", testcmd=["cd /home/z00293696/works/source/testsuite/lmbench/lmbench-3.0-a9; make rerun"])

	run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry=ilp32_disabled, total_count=1, test_user="root", testcmd=["cd /home/z00293696/speccpu2006;. ./shrc; runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=ref --noreportable --tune=base --iterations=1 perlbench bzip2 gcc mcf gobmk hmmer sjeng libquantum h264ref omnetpp astar xalancbmk"])
	#run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry=ilp32-disabled, total_count=1, test_user="root", testcmd=["cd /home/z00293696/speccpu2006;. ./shrc; runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=ref --noreportable --tune=base --iterations=1 mcf hmmer"])

	run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry=no_ilp32, total_count=1, test_user="root", testcmd=["cd /home/z00293696/speccpu2006;. ./shrc; runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=ref --noreportable --tune=base --iterations=1 perlbench bzip2 gcc mcf gobmk hmmer sjeng libquantum h264ref omnetpp astar xalancbmk"])
	#run_benchmark(host="D03-02", normal_user="z00293696", root_user="root", grubentry=no_ilp32, total_count=1, test_user="root", testcmd=["cd /home/z00293696/speccpu2006;. ./shrc; runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=ref --noreportable --tune=base --iterations=1 mcf"], reboot=False)
	round_cur = round_cur + 1

