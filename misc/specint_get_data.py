#!/usr/bin/env python

from __future__ import print_function
import sys
import re
import glob
import getopt
import os	#for os.path.isdir
import numpy

def format_percentage(number):
	number = number * 100
	if number >= 0:
		return " %.2f%%" % number
	else:
		return "%.2f%%" % number

def specint_avg(paths, names):
#	paths = ["/home/z00293696/works/source/testsuite/testresult/ilp32/20161022_1024_specint_LP64/ILP32_disabled"]
	globs = "/CINT2006.*.ref.txt"

	result={}
	for path in paths:
		if os.path.isdir(path):
			files = glob.glob(path + globs)
		else:
			files = glob.glob(path)

		for fn in files:
			f = open(fn)
			lines = f.readlines()
			specint_result=False
			for line in lines:
				if re.match("======*", line):
					specint_result=True
					continue

				if specint_result:
					#400.perlbench    9770        770      12.7  *
					if names:
						for name in names:
							if re.match(r'^' + name, line):
								if re.match(r'^[0-9][0-9][0-9].*\*', line):
									m = re.match(r'([0-9][0-9][0-9]\.[a-z0-9]+) *[0-9]+ *[0-9]+ *([0-9]+\.[0-9]+)', line)
									if not m.group(1) in result:
										l = []
										l.append(float(m.group(2)))
										result[m.group(1)] = l
									else:
										result[m.group(1)].append(float(m.group(2)))

	avgs = {}
	cv = {}
	for n, v in result.iteritems():
		avgs[n] = sum(v)/len(v)
		cv[n] = format_percentage(numpy.std(v) / avgs[n])

	return (avgs, cv)

def diff(result1, result2):
	diff = {}
	for n, v in result1.items():
		if n in result1 and n in result2:
			d = (result1[n] - result2[n]) / result2[n]
			diff[n] = format_percentage(d)
		else:
			if not n in result1:
				print(n + " does exist in result1, skip")
			if not n in result2:
				print(n + " does exist in result2, skip")

	return diff

def specint_diff(t1, t2, names):
	if not t1 or not t2:
		print("testresult or testbase is empty, exit")
		sys.exit(2)

	(s1, cv1) = specint_avg(t1, names)
	(s2, cv2) = specint_avg(t2, names)
#	print("Original numbers:")
#	print(s1)
#	print(cv1)
#	print(s2)
#	print(cv2)

	diff_result = diff(s1, s2)
	keys = diff_result.keys()
	keys.sort()

	max_len_of_key = 0
	for key in keys:
		if len(key) > max_len_of_key:
			max_len_of_key = len(key)

	print("")
	print("Diff:")
	print(t1)
	print("%*s: %s %s %s %s" % (max_len_of_key + 2, "testcases", "increase", "cv(base)", "cv(result)", "cv: Coefficient of Variation"))
	for key in keys:
		print("%*s:  %s  %s   %s" % (max_len_of_key + 2, key, diff_result[key], cv1[key], cv2[key]))

def usage(argv):
	print("Usage:")
	print(argv[0] + ": --testresult /path/to/testresult --testbase /path/to/testbase")
	print("output the average and the diff of (avg(testresult) - arg(testbase))/avg(testbase)")
	print("--testresult: the path of test result. support multi paths")
	print("--testbase: the path of test base. support multi paths")

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "h", ["testresult=", "testbase="])
	except getopt.GetoptError as e:
		print("Argument error " + e.opt + ": " + e.msg)
		usage(argv)
		sys.exit(2)

	testresult = []
	testbase = []
	for opt, arg in opts:
		if opt == "-h":
			usage(argv)
			sys.exit(2)
		elif opt == "--testresult":
			testresult.append(arg)
		elif opt == "--testbase":
			testbase.append(arg)

	print("The test result:")
	print(testresult)
	print("The test base:")
	print(testbase)
	full_name = ["400.perlbench",  "401.bzip2",  "403.gcc",  "429.mcf",  "445.gobmk",  "456.hmmer",  "458.sjeng",  "462.libquantum",  "464.h264ref",  "471.omnetpp",  "473.astar",  "483.xalancbmk"]
	specint_diff(testresult, testbase, full_name)


if __name__ == "__main__":
	main(sys.argv[1:])

