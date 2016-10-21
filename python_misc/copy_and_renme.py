#!/usr/bin/env python

from __future__ import print_function
import shutil
import sys
import os
import re

def copy_file_with_og(src, dst):
	print("copy " + src + "to " + dst)
	shutil.copy2(src, dst)
	st = os.stat(src)
	os.chown(dst, st.st_uid, st.st_gid)

src=sys.argv[1]
dst=sys.argv[2]
offset=sys.argv[3]

for root, dirs, files in os.walk(src):
	for f in files:
		match = re.match(r'(localhost\.)([0-9])', f)
		if match:
			filename=match.group(1)
			subfix=match.group(2)

		print(subfix)
		subfix = int(subfix) + int(offset)
		print(subfix)
		src_file=os.path.join(root, f)
		dst_file=os.path.join(dst, filename + str(subfix))
		copy_file_with_og(src_file, dst_file)

