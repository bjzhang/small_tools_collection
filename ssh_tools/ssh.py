#!/usr/bin/env python
#http://stackoverflow.com/questions/3462143/get-difference-between-two-lists/3462160#3462160
#In [5]: list(set(temp1) - set(temp2))
#Out[5]: ['Four', 'Three']

#TODO: 
#1.  seperate the lmbench and specint log.
#2.  decrease the arguments of function. It is hard to maintain currently.

from __future__ import print_function
import paramiko
import time
import logging
import select
import datetime
import progressbar
import os
import sys	#for exit
import subprocess
import json	#for json.load
import traceback#for print function name through extract_stack

from pprint import pprint	#for pprint.pprint

debug=False
test_mode=False

def function_name():
	#ref <http://stackoverflow.com/questions/251464/how-to-get-a-function-name-as-a-string-in-python>
	return traceback.extract_stack(None, 2)[0][2]

def run_cmd_block(cmd):
	subprocess.check_call(args = cmd)

def ssh_cmd(host, user, cmd, slient=True):
#	print("Testing on " + host + " with user: " + user + " cmd: <" + cmd + ">")
#	logging.getLogger("paramiko").setLevel(logging.WARNING) ssh = paramiko.SSHClient()
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, username=user, timeout=120)
	for i, c in enumerate(cmd):
		if not slient:
			print(c)
		stdin,stdout,stderr = ssh.exec_command(c)
		if not slient:
			print("stdout: " + str(stdout.readlines()))

		for s in stderr.readlines():
			if len(s) > 0:
				print(s, end="")
#		print("stderr: " + str(stderr.readlines()))

def ssh_cmd_get_log(host, user, cmd):
#	print("Testing on " + host + " with user: " + user + " cmd: <" + cmd + ">")
#	logging.getLogger("paramiko").setLevel(logging.WARNING) ssh = paramiko.SSHClient()
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, username=user, timeout=120)
	result = []
	for i, c in enumerate(cmd):
		stdin,stdout,stderr = ssh.exec_command(c)
		r = stdout.readlines()
		result = result + r

	return result

def ssh_wait_connection(host, normal_user, dry_run=False):
	while True:
		try:
			ssh_cmd(host, normal_user, ["echo -n"])
			break
		except:
			print(".", end="")
			time.sleep(10)

def ssh_transport(host, user, cmd, dry_run=False, silent=False):
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, username=user, timeout=120)
	transport = ssh.get_transport()
	for i, c in enumerate(cmd):
		print(c)
		channel = transport.open_session()
		channel.get_pty()
		channel.exec_command(c)
		while True:
			r, w, x = select.select([channel], [], [], 0.0)
			if len(r) > 0:
				s = channel.recv(1024)
				if len(s) > 0:
					if not silent:
						print(s, end="")
				else:
					break
		if channel.recv_stderr_ready():
			s = channel.recv_stderr(1024)
			if len(s) > 0:
				print(s, end="")

def ssh_reboot(host, normal_user, root_user):
	print("Rebooting...")
	ssh_cmd(host, root_user, ["reboot"], False)
	while True:
		try:
			ssh_cmd(host, normal_user, ["echo -n"])
			print(".", end="")
			time.sleep(1)
		except:
			break
	print("Waiting for reboot: ", end="")
	ssh_wait_connection(host, normal_user)
	print("done")

def scp(host, user, src, dst, silent=True):
	def progress(so_far, total):
		pbar.update(float(so_far) / float(total) * 100)

	#host="D03-02"
	#user="z00293696"
	#src="/mnt/opensuse_leap42.1_aarch64_10.qcow2/2/"
	#dst="/home/z00293696/works/root"
	dst_dir=os.path.dirname(dst)
	print("scp " + src + " " + user + "@" + host + ":" + dst)

	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, username=user, timeout=120, compress=True)
	stdin,stdout,stderr = ssh.exec_command("mkdir -p " + dst_dir)
	s = stdout.readlines()
	if len(s) > 0:
		print(s, end="")
	s = stderr.readlines()
	if len(s) > 0:
		print(s, end="")

	sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
	pbar = progressbar.ProgressBar(maxval=100).start()
	sftp.put(src, dst, progress)
	#TODO: chmod, chown
	pbar.finish()

def scp_s2s(src, src_user, dst, dst_user, src_path, dst_path, dryrun=False):

	cmd = ['scp', '-p', src_user + "@" + src + ":" + src_path, dst_user + "@" + dst + ":" + dst_path]
	print(cmd)
	if dryrun:
		return

	ssh_cmd(dst, dst_user, ['mkdir -p ' + os.path.dirname(dst_path)], slient=True)
	run_cmd_block(cmd)

def run_benchmark(host, normal_user, root_user, grubentry, total_count, test_user, testcmd, reboot=True, silent=False):
	print(host)
	print(normal_user)
	print(grubentry)
	print(total_count)
	print(test_user)
	dt = datetime.datetime.now()
	print("test start at " + str(dt))
	for i, el in enumerate(testcmd):
		print(el)

	ssh_wait_connection(host, normal_user)
	print("Connection correct, starting...")
	if reboot:
		print("Change grub.cfg before reboot")
		ssh_cmd(host, root_user, ['sed -i "s/^set.default.*$/set default=' + grubentry + '/g" /boot/EFI/grub2/grub.cfg'], False)
		print("result")
		ssh_cmd(host, normal_user, ["grep " + grubentry + " /boot/EFI/grub2/grub.cfg"], False)
		ssh_reboot(host, normal_user, root_user)
	else:
		print("Skip reboot")

	print("Current machine")
	ssh_cmd(host, normal_user, ["uname -a"], False)
	ssh_cmd(host, normal_user, ["zgrep ILP32 /proc/config.gz"], False)

	count = 0
	while(count < total_count):
		print("count is " + str(count))
		ssh_transport(host, test_user, testcmd, silent=silent)
		count = count + 1

	dt = datetime.datetime.now()
	print("test finish at " + str(dt))

def compile_kernel(host, user, path, commit, extra_config, dry_run=False, silent=False, checkout_force=False, dryrun=False):
	dt = datetime.datetime.now()
	print("compile_kernel start at " + str(dt))

	if not dryrun:
		ssh_wait_connection(host, user, dry_run)

		cmd="cd " + path + "; git checkout -f " + commit
		ssh_transport(host, user, [cmd], dry_run, silent=silent)

		cmd="export PATH=/home/z00293696/works/source/linux_toolkit/bin:/home/z00293696/works/software/ilp32-gcc/20160612_little_endian_toolchain/install/bin:$PATH; cd " + path + "; kernel_build --path " + path + " --disable install_header_to_cc"
		for i, extra in enumerate(extra_config):
			cmd = cmd + " --extra " + extra

		ssh_transport(host, user, [cmd], dry_run, silent=silent)

	print("compile_kernel end at " + str(dt))

def get_files(folder):
        for root, subFolders, files in os.walk(folder):
                if root == folder:
                        return files

def remote_copy_log_file(src, src_user, dst, dst_user, src_dir, dst_dir, files, silent=True):
	run_cmd_block(['mkdir', '-p', dst_dir])
	for f in files:
		p = src_dir + "/" + f.rstrip('\n')
		if not silent:
			print("scp -p " + src_user + "@" + src + ":" + src_dir + "/" + f + " " + dst_user + "@" + dst + ":" + dst_dir)
		scp_s2s(src, src_user, dst, dst_user, p, dst_dir + "/" + f.rstrip('\n'))

def run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, this_grubentry, count, test_cmd, log_cmd, log_dir, host_log_dir, silent=False, reboot=True, dryrun=False):
	if dryrun:
		print(function_name())
		return

	if log_cmd:
		olds = ssh_cmd_get_log(host=guest, user=guest_user, cmd=log_cmd)

	run_benchmark(host=guest, normal_user=guest_user, root_user=guest_root, grubentry=this_grubentry, total_count=count, test_user=guest_root, testcmd=test_cmd, silent=silent, reboot=reboot)
	if log_cmd:
		news = ssh_cmd_get_log(host=guest, user=guest_user, cmd=log_cmd)
		new_logs = list(set(news) - set(olds))
		print(new_logs)
		remote_copy_log_file(guest, guest_user, host, host_user, log_dir, host_log_dir, new_logs)

def run_test(config, dryrun=False):
	server = config["server"]
	kernel = config["kernel"]
	test = config["test"]
	if debug:
		pprint(server)
		pprint(kernel)
		pprint(test)

	for commit in kernel["commits"]:
		if server and "log_base" in server:
			log_path = server["log_base"] + "/" + commit["commit"] + "_" + commit["name"]

		#do not return if no kernel configure, we may run with the existing kernel in the machine.
		if kernel and "path" in kernel:
			image_path = kernel["path"] + "/arch/arm64/boot/Image"
			config_path = kernel["path"] + "/.config"
			compile_kernel(kernel["host"], kernel["user"], kernel["path"], commit["commit"], kernel["config_fragment"], silent=True, dryrun=dryrun)
			if test and "kernel_install" in test:
				scp_s2s(kernel["host"], kernel["user"], test["host"], test["root"], image_path, test["kernel_install"], dryrun=dryrun)
				scp_s2s(kernel["host"], kernel["user"], server["host"], server["user"], image_path, log_path + "/" + commit["commit"] + "_" + commit["name"] + "_Image", dryrun=dryrun)
				scp_s2s(kernel["host"], kernel["user"], server["host"], server["user"], config_path, log_path + "/" + commit["commit"] + "_" + commit["name"] + "_config", dryrun=dryrun)
			else:
				print("SKIP: install kernel and save kernel Image/config")
		else:
			print("skip compile kernel")

		if test and "testsuite" in test:
			run_benchmark_and_get_log(server["host"], server["user"], test["host"], test["user"], test["root"], test["grub"], test["total_test_count"], test["testsuite"], test["log_cmd"], test["log_dir"], log_path, dryrun=dryrun)
		else:
			print("skip: run benchmark")

def test():
	host="localhost"
	host_user="z00293696"
	ssh_transport(host, host_user, ["ls"])
	ssh_transport(host, host_user, ["sleep 1"])

	#guest="d03-09"
	#guest_user="z00293696"
	#guest_root="root"
	#testsuite=["cd /home/z00293696/works; ls; screen -L ls source/kernel"]
	#run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, "", 1, testsuite, "", "", "", reboot=False)

	#testsuite=["echo sleep start; screen -L sleep 2; echo sleep done"]
	#run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, "", 1, testsuite, "", "", "", reboot=False)

	print("FULL DRYRUN")
	server = {u'host': u'bj23_new', u'log_base': u'/home/z00293696/works/source/testsuite/testresult/ilp32/20161104_specint_LP64_ilp32_on_aarch32_on', u'user': u'z00293696'}
	kernel = {u'commits': [{u'commit': u'afb510f', u'name': u'ilp32_merged'}, {u'commit': u'a5ba168', u'name': u'ilp32_unmerged'}], u'config_fragment': [u'kernel_el0_config', u'kernel_ilp32_config', u'kernel_disable_arm_smmu_v3_config'], u'host': u'heyunlei', u'path': u'/home/z00293696/works/source/kernel/hulk', u'user': u'z00293696'}
	test = {u'grub': u'z00293696-ilp32-test', u'host': u'D03-02', u'kernel_install': u'/boot/z00293696-ilp32-test', u'log_cmd': [u'cd /home/z00293696/speccpu2006/result; ls'], u'log_dir': u'/home/z00293696/speccpu2006/result', u'root': u'root', u'testsuite': [u'cd /home/z00293696/speccpu2006;. ./shrc; screen -L runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=test,train,ref --noreportable --tune=base,peak --iterations=3 --verbose 0 bzip2 mcf hmmer libquantum'], u'total_test_count': 1, u'user': u'z00293696'}
	config = {"server": server, "kernel": kernel, "test": test}
	run_test(config, dryrun=True)

	print("\nDRYRUN: skip kernel compile")
	path=config["kernel"].pop("path")
	run_test(config, dryrun=True)

	print("\nDRYRUN: skip kernel install")
	config["kernel"]["path"] = path
	del config["test"]["kernel_install"]
	run_test(config, dryrun=True)

	print("\nDRYRUN: skip run benchmark")
	del config["test"]["testsuite"]
	run_test(config, dryrun=True)

	sys.exit()

print("START")
if test_mode:
	print("TEST")
	test()
else:
	with open(sys.argv[1], 'r') as fp:
		config = json.load(fp)

	run_test(config)

	with open('config.json', 'w') as fp:
		json.dump(config, fp)

print("END")

