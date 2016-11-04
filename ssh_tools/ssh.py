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

def scp_s2s(src, src_user, dst, dst_user, src_path, dst_path):
	cmd = ['scp', '-p', src_user + "@" + src + ":" + src_path, dst_user + "@" + dst + ":" + dst_path]
	print(cmd)
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

def compile_kernel(host, user, path, commit, extra_config, dry_run=False, silent=False):
	dt = datetime.datetime.now()
	print("compile_kernel start at " + str(dt))

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

def run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, this_grubentry, count, test_cmd, log_cmd, log_dir, host_log_dir, silent=False, reboot=True):
	if log_cmd:
		olds = ssh_cmd_get_log(host=guest, user=guest_user, cmd=log_cmd)

	run_benchmark(host=guest, normal_user=guest_user, root_user=guest_root, grubentry=this_grubentry, total_count=count, test_user=guest_root, testcmd=test_cmd, silent=silent, reboot=reboot)
	if log_cmd:
		news = ssh_cmd_get_log(host=guest, user=guest_user, cmd=log_cmd)
		new_logs = list(set(news) - set(olds))
		print(new_logs)
		remote_copy_log_file(guest, guest_user, host, host_user, log_dir, host_log_dir, new_logs)

def run_test(server, kernel, test):
	for commit in kernel["commits"]:
		log_path = server["log_base"] + "/" + commit + "_" + server["log_subfix"]

		image_path = kernel["path"] + "/arch/arm64/boot/Image"
		config_path = kernel["path"] + "/.config"
		compile_kernel(kernel["host"], kernel["user"], kernel["path"], commit, kernel["config_fragment"], silent=True)
		scp_s2s(kernel["host"], kernel["user"], test["host"], test["root"], image_path, test["kernel_install"])
		scp_s2s(kernel["host"], kernel["user"], server["host"], server["user"], image_path, log_path + "/" + commit + "_" + server["log_subfix"] + "_Image")
		scp_s2s(kernel["host"], kernel["user"], server["host"], server["user"], config_path, log_path + "/" + commit + "_" + server["log_subfix"] + "_config")

		run_benchmark_and_get_log(server["host"], server["user"], test["host"], test["user"], test["root"], test["grub"], test["total_test_count"], test["testsuite"], test["log_cmd"], test["log_dir"], log_path)

def test():
	host="localhost"
	host_user="z00293696"
	#ssh_transport(host, host_user, ["ls"])
	#ssh_transport(host, host, ["sleep 1"])

	guest="d03-02"
	guest_user="z00293696"
	guest_root="root"
	testsuite=["cd /home/z00293696/works; ls; screen -L ls source/kernel"]
	run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, "", 1, testsuite, "", "", "", reboot=False)

	testsuite=["echo sleep start; screen -L sleep 2; echo sleep done"]
	run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, "", 1, testsuite, "", "", "", reboot=False)
	sys.exit()

lmbench=["cd /home/z00293696/works/source/testsuite/lmbench/lmbench-3.0-a9; screen -L make rerun"]
specint=["cd /home/z00293696/speccpu2006;. ./shrc; screen -L runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=test,train,ref --noreportable --tune=base,peak --iterations=3 --verbose 0 bzip2 mcf hmmer libquantum"]
lmbench_log_dir="/home/z00293696/works/source/testsuite/lmbench/lmbench-3.0-a9/results/aarch64-linux-gnu"
lmbench_log_cmd=['cd ' + lmbench_log_dir + '; ls']
specint_log_dir="/home/z00293696/speccpu2006/result"
specint_log_cmd=['cd ' + specint_log_dir + '; ls']

kernel_server="heyunlei"
kernel_server_user="z00293696"
host="bj23_new"
host_user="z00293696"
guest="D03-02"
guest_user="z00293696"
guest_root="root"
kernel_path="/home/z00293696/works/source/kernel/hulk"
kernel_install="/boot/z00293696-ilp32-test"
grub="z00293696-ilp32-test"
config=["kernel_el0_config", "kernel_ilp32_config", "kernel_disable_arm_smmu_v3_config"]
config_name="aarch32_on_ilp32_on"

testsuite=specint
#List the directory, run_benchmark_and_get_log will compare the filename after test and copy the new file.
testsuite_log_cmd=specint_log_cmd
testsuite_log_dir=specint_log_dir

#test()
print("START")
log_base = "/home/z00293696/works/source/testsuite/testresult/ilp32/20161103_specint_LP64"
#commits=["afb510f", "a5ba168", "b5107ca"]
commits=["afb510f", "a5ba168"]
config = ["kernel_disable_compat_config", "kernel_disable_aarch32_el0_config", "kernel_disable_arm64_ilp32_config", "kernel_disable_arm_smmu_v3_config"]
kernel = {"host": kernel_server, "user": kernel_server_user, "path": kernel_path, "commits": commits, "config_fragment": config}
server = {"host": host, "user": host_user, "log_base": log_base, "log_subfix": config_name}
test =   {"host": guest, "user": guest_user, "root": guest_root, "grub": grub, "kernel_install": kernel_install, "total_test_count": 1, "testsuite": testsuite, "log_cmd": testsuite_log_cmd, "log_dir": testsuite_log_dir}

#skip h264ref because it always fail
run_test(server, kernel, test)

log_base = "/home/z00293696/works/source/testsuite/testresult/ilp32/20161103_lmbench_LP64"
kernel = {"host": kernel_server, "user": kernel_server_user, "path": kernel_path, "commits": commits, "config_fragment": config}
server = {"host": host, "user": host_user, "log_base": log_base, "log_subfix": config_name}
test =   {"host": guest, "user": guest_user, "root": guest_root, "grub": grub, "kernel_install": kernel_install, "total_test_count": 5, "testsuite": lmbench, "log_cmd": lmbench_log_cmd, "log_dir": lmbench_log_dir}
run_test(server, kernel, test)
print("END")

