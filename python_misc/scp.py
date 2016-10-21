#!/usr/bin/env python
from __future__ import print_function
import paramiko
import time
import progressbar

def progress(so_far, total):
	pbar.update(float(so_far) / float(total) * 100)

host="D03-02"
user="z00293696"
src="/mnt/opensuse_leap42.1_aarch64_10.qcow2/2/"
dst="/home/z00293696/works/root"
dst_dir="/home/z00293696/works"

ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, timeout=120, compress=True)
stdin,stdout,stderr = ssh.exec_command("mkdir -p " + dst_dir)
print("stdout: " + str(stdout.readlines()))
print("stderr: " + str(stderr.readlines()))

sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
pbar = progressbar.ProgressBar(maxval=100).start()
sftp.put(src, dst, progress)
pbar.finish()

