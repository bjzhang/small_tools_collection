#!/usr/bin/env python
#http://stackoverflow.com/questions/3462143/get-difference-between-two-lists/3462160#3462160
#In [5]: list(set(temp1) - set(temp2))
#Out[5]: ['Four', 'Three']

from __future__ import print_function
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

#Basic function which is not relative to the specific function of this script
def function_name():
	#ref <http://stackoverflow.com/questions/251464/how-to-get-a-function-name-as-a-string-in-python>
	return traceback.extract_stack(None, 2)[0][2]

def print_flush(s):
	print(s, end="")
	sys.stdout.flush()

def run_cmd_block(cmd, is_true_shell=False):
	subprocess.check_call(args = cmd, shell=is_true_shell)

def run_cmd_block_output(cmd, is_true_shell=False):
	return subprocess.check_output(args = cmd, stderr=subprocess.STDOUT, shell=is_true_shell)

def ssh_cmd(host, user, cmd, extra_opts="", silent=True, is_true_shell=False, allow_fail=False):
	for i, c in enumerate(cmd):
		current_cmd = ['ssh ' + extra_opts + ' ' + user + '@' + host + ' \'' + c + '\'']
		if not silent:
			print(current_cmd)

		try:
			run_cmd_block(current_cmd, is_true_shell)
		except subprocess.CalledProcessError:
			#Subprocess think reboot is failure. It is because of disconnecting of ssh.
			if allow_fail:
				pass
			else:
				raise

#Return list of file through the given cmd on user@host
def ssh_cmd_get_log(host, user, cmd):
	ssh_wait_connection(host, user)
	if isinstance(cmd, unicode):
		cmd = cmd.encode("utf-8")

	result = []
	for i, c in enumerate(cmd):
		current_cmd = ['ssh ' + user + '@' + host + ' \"' + c + '\"']
		r = run_cmd_block_output(current_cmd, is_true_shell=True)
		result = result + r.splitlines()

	return result

def ssh_wait_connection(host, normal_user, dry_run=False, debug=False):
	if debug:
		print("host: " + host + "; user: " + normal_user)
	while True:
		try:
			ssh_cmd(host, normal_user, ["echo -n"], is_true_shell=True)
			break
		except:
			print(".", end="")
			time.sleep(10)

def ssh_transport(host, user, cmd, extra_opts="", dry_run=False, silent=False):
	ssh_cmd(host, user, cmd, extra_opts=extra_opts, is_true_shell=True)

#Basic function end

def ssh_reboot(host, normal_user, root_user):
	print("Rebooting...")
	ssh_cmd(host, root_user, ["reboot"], silent=False, is_true_shell=True, allow_fail=True)

	while True:
		try:
			ssh_cmd(host, normal_user, ["echo -n"], is_true_shell=True)
			print(".", end="")
			time.sleep(10)
		except:
			break
	print("Waiting for reboot: ")
	ssh_wait_connection(host, normal_user)
	print("done")

def scp_s2s(src, src_user, dst, dst_user, src_path, dst_path, dryrun=False):
	cmd = ['scp', '-pr', src_user + "@" + src + ":" + src_path, dst_user + "@" + dst + ":" + dst_path]
	print(cmd)
	if dryrun:
		return

	if False:
		print("create dir if needed " + os.path.dirname(dst_path))

	ssh_cmd(dst, dst_user, ['mkdir -p ' + os.path.dirname(dst_path)], silent=True, is_true_shell=True)
	run_cmd_block(cmd)

def run_benchmark(host, normal_user, root_user, grubentry, total_count, test_user, testcmd, grub_cfg, reboot=True, silent=False):
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
		ssh_cmd(host, root_user, ['sed -i "s/^set.default.*$/set default=' + grubentry + '/g" ' + grub_cfg], silent=False, is_true_shell=True)
		print("result")
		ssh_cmd(host, normal_user, ["grep " + grubentry + " " + grub_cfg], silent=False, is_true_shell=True)
		ssh_reboot(host, normal_user, root_user)
	else:
		print("Skip reboot")

	print("Current machine")
	ssh_cmd(host, normal_user, ["uname -a"], silent=False, is_true_shell=True)
	ssh_cmd(host, normal_user, ["zgrep CONFIG_COMPAT /proc/config.gz"], silent=False, is_true_shell=True, allow_fail=True)
	ssh_cmd(host, normal_user, ["zgrep CONFIG_AARCH32_EL0 /proc/config.gz"], silent=False, is_true_shell=True, allow_fail=True)
	ssh_cmd(host, normal_user, ["zgrep CONFIG_ARM64_ILP32 /proc/config.gz"], silent=False, is_true_shell=True, allow_fail=True)

	count = 0
	while(count < total_count):
		print("count is " + str(count))
		ssh_transport(host, test_user, testcmd, extra_opts="-t", silent=silent)
		count = count + 1

	dt = datetime.datetime.now()
	print("test finish at " + str(dt))

def compile_kernel(host, user, path, commit, config_enable, config_disable="", dry_run=False, silent=False, checkout_force=False, dryrun=False):
	dt = datetime.datetime.now()
	print("compile_kernel start at " + str(dt))
	config_enable = config_enable.encode("utf-8")
	config_disable = config_disable.encode("utf-8")

	if not dryrun:
		ssh_wait_connection(host, user, dry_run, debug=True)

#		tools="/home/bamvor/works/source/small_tools_collection"
#		try:
#			cmd="cd " + tools + "; git pull"
#			ssh_transport(host, user, [cmd], dry_run=dry_run, silent=silent)
#		except subprocess.CalledProcessError:
#			print("Update tools failed when run the following cmd: " + cmd)

		try:
			cmd="cd " + path + "; git checkout -f " + commit
			ssh_transport(host, user, [cmd], dry_run=dry_run, silent=silent)
		except subprocess.CalledProcessError:
			print("Check out kernel source failed when run the following cmd: " + cmd)

		cmd="PATH=$PATH:/home/bamvor/works/software/toolchain/gcc-linaro-6.2.1-2016.11-x86_64_aarch64-linux-gnu/gcc-linaro-6.2.1-2016.11-x86_64_aarch64-linux-gnu/bin:/home/z00293696/works/source/small_tools_collection/build/kernel:/home/z00293696/works/reference/small_tools_collection/build/kernel:/home/bamvor/works/source/small_tools_collection/build/kernel; cd " + path + "; git am 0001-remove-mmc2-on-hikey-dts.patch; echo $PATH; build.sh " + path + " " + config_enable
		if config_disable:
			cmd = cmd + " " + config_disable

		ssh_transport(host, user, [cmd], dry_run=dry_run, silent=silent)

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

#Do not save log when log_cmd is False
def run_benchmark_and_get_log(host, host_user, test, host_log_dir, silent=False, reboot=True, dryrun=False):
	if dryrun:
		print(function_name())
		return

	if "log_pre" in test:
		ssh_cmd(host=test["host"], user=test["root"], cmd=[test["log_pre"]], is_true_shell=True)

	if "log_cmd" in test:
		olds = ssh_cmd_get_log(host=test["host"], user=test["user"], cmd=test["log_cmd"])

	run_benchmark(host=test["host"], normal_user=test["user"], root_user=test["root"], grubentry=test["grub"], total_count=test["total_test_count"], test_user=test["root"], testcmd=test["testsuite"], grub_cfg=test["grub_cfg"], silent=silent, reboot=reboot)
	if "log_cmd" in test:
		news = ssh_cmd_get_log(host=test["host"], user=test["user"], cmd=test["log_cmd"])
		new_logs = list(set(news) - set(olds))
		print(new_logs)
		remote_copy_log_file(test["host"], test["root"], host, host_user, test["log_dir"], host_log_dir, new_logs)

#Check the environment before the script run.
def env_check(config):
	empty_echo = "echo -n"

	print("Environment test, include ssh(scp) connection test, essential command test")
	print_flush("Test connection to server: ")
	ssh_cmd(config["server"]["host"], config["server"]["user"], [empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")
	print_flush("Test connection to kernel build machine: ")
	ssh_cmd(config["kernel"]["host"], config["kernel"]["user"], [empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")
	print_flush("Test connection to test machine with normal user: ")
	ssh_cmd(config["test"]["host"], config["test"]["user"], [empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")
	print_flush("Test connection to test machine with normal root: ")
	ssh_cmd(config["test"]["host"], config["test"]["root"], [empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")
	print_flush("Whether 'screen' command is existed in test machine: ")
	try:
		ssh_cmd(config["test"]["host"], config["test"]["user"], ["screen sleep 1", "screen " + empty_echo], extra_opts="-t", silent=not debug, is_true_shell=True)
		print("Successful")
	except subprocess.CalledProcessError:
		print("Fail: check screen command in your test machine " + config["test"]["host"])
	print_flush("Test ssh from kernel to test: ")
	ssh_cmd(config["kernel"]["host"], config["kernel"]["user"], ["ssh " + config["test"]["user"] + "@" + config["test"]["host"] + " " + empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")
	print_flush("Test ssh from kernel to server: ")
	ssh_cmd(config["kernel"]["host"], config["kernel"]["user"], ["ssh " + config["server"]["user"] + "@" + config["server"]["host"] + " " + empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")
	print_flush("Test ssh from test to server: ")
	ssh_cmd(config["test"]["host"], config["test"]["user"], ["ssh " + config["server"]["user"] + "@" + config["server"]["host"] + " " + empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")
	print_flush("Test ssh from test(root) to server: ")
	ssh_cmd(config["test"]["host"], config["test"]["root"], ["ssh " + config["server"]["user"] + "@" + config["server"]["host"] + " " + empty_echo], silent=not debug, is_true_shell=True)
	print("Successful")

#Run the test according to config. If fail, please set "test_mode=False" in the beginning of this file.
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
			if "log_base_with_time" in server and int(server["log_base_with_time"]) == 1:
				log_path = log_path + "_" + datetime.datetime.now().strftime('%Y%m%d_%H%M')

		#do not return if no kernel configure, we may run with the existing kernel in the machine.
		if kernel and "path" in kernel:
			image_path = kernel["path"] + "/arch/arm64/boot/Image"
			config_path = kernel["path"] + "/.config"
			compile_kernel(kernel["host"], kernel["user"], kernel["path"], commit["commit"], kernel["config_enable"], kernel["config_disable"], silent=True, dryrun=dryrun)
			if test and "kernel_install" in kernel:
				scp_s2s(kernel["host"], kernel["user"], test["host"], test["root"], image_path, kernel["kernel_install"], dryrun=dryrun)
				if "dtb_path" in kernel:
					scp_s2s(kernel["host"], kernel["user"], test["host"], test["root"], kernel["path"] + "/" + kernel["dtb_path"], kernel["dtb_install"], dryrun=dryrun)
				if "modules_path" in kernel:
					scp_s2s(kernel["host"], kernel["user"], test["host"], test["root"], kernel["path"] + "/" + kernel["modules_path"], kernel["modules_install"], dryrun=dryrun)
				scp_s2s(kernel["host"], kernel["user"], server["host"], server["user"], image_path, log_path + "/" + commit["commit"] + "_" + commit["name"] + "_Image", dryrun=dryrun)
				scp_s2s(kernel["host"], kernel["user"], server["host"], server["user"], config_path, log_path + "/" + commit["commit"] + "_" + commit["name"] + "_config", dryrun=dryrun)
			else:
				print("SKIP: install kernel and save kernel Image/config")
		else:
			print("skip compile kernel")

		if test and "testsuite" in test:
			if test and "not_reboot" in test:
				reboot=False
			else:
				reboot=True

			run_benchmark_and_get_log(server["host"], server["user"], test, log_path, dryrun=dryrun, reboot=reboot)
		else:
			print("skip: run benchmark")

def test():
	host="localhost"
	host_user="z00293696"
	ssh_transport(host, host_user, ["ls"])
	ssh_transport(host, host_user, ["sleep 1"])
	ssh_cmd(host, host_user, ["ls", "sleep 1", "echo 886"], is_true_shell=True)

	olds = ssh_cmd_get_log(host, host_user, ["ls"])
	print(olds)
	print(type(olds))
	news = ssh_cmd_get_log(host, host_user, ["ls -a"])
	print(news)
	new_logs = list(set(news) - set(olds))
	print(new_logs)

	#FIXME: it could not be used for current run_benchmark_and_get_log
	#guest="d03-09"
	#guest_user="z00293696"
	#guest_root="root"
	#testsuite=["cd /home/z00293696/works; ls; screen -L ls source/kernel"]
	#run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, "", 1, testsuite, "", "", "", reboot=False)

	#testsuite=["echo sleep start; screen -L sleep 2; echo sleep done"]
	#run_benchmark_and_get_log(host, host_user, guest, guest_user, guest_root, "", 1, testsuite, "", "", "", reboot=False)

	print("FULL DRYRUN")
	server = {u'host': u'bj23', u'log_base': u'/home/z00293696/works/source/testsuite/testresult/ilp32/20161104_specint_LP64_ilp32_on_aarch32_on', u'user': u'z00293696'}
	kernel = {u'commits': [{u'commit': u'afb510f', u'name': u'ilp32_merged'}, {u'commit': u'a5ba168', u'name': u'ilp32_unmerged'}], u'config_fragment': [u'kernel_el0_config', u'kernel_ilp32_config', u'kernel_disable_arm_smmu_v3_config'], u'host': u'heyunlei', u'path': u'/home/z00293696/works/source/kernel/hulk', u'user': u'z00293696'}
	test = {u'grub': u'z00293696-ilp32-test', u'host': u'D03-02', u'kernel_install': u'/boot/z00293696-ilp32-test', u'log_cmd': [u'cd /home/z00293696/speccpu2006/result; ls'], u'log_dir': u'/home/z00293696/speccpu2006/result', u'root': u'root', u'testsuite': [u'cd /home/z00293696/speccpu2006;. ./shrc; screen -L runspec --config=Arm64-single-core-linux64-arm64-lp64-gcc49.cfg --size=test,train,ref --noreportable --tune=base,peak --iterations=3 --verbose 0 bzip2 mcf hmmer libquantum'], u'total_test_count': 1, u'user': u'z00293696'}
	config = {"server": server, "kernel": kernel, "test": test}

	print("Environment check")
	env_check(config)

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
	i = 1;
	while i < len(sys.argv):
		print(sys.argv[i])
		with open(sys.argv[i], 'r') as fp:
			config = json.load(fp)
		env_check(config)
		run_test(config)
		with open('config.json', 'w') as fp:
			json.dump(config, fp, indent=4, sort_keys=True)
		i = i + 1
print("END")

