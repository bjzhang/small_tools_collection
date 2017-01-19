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
		return " %6.2f%%" % number
	else:
		return "%6.2f%%" % number

#return dictionary of average and cv
def get_avg(paths, names):
	globs = "/perf_stat"
	result={}

	for path in paths:
		if os.path.isdir(path):
			files = glob.glob(path + globs)
		else:
			files = glob.glob(path)

		for fn in files:
			f = open(fn)
			lines = f.readlines()
			for line in lines:
				#24876432 iTLB-load-misses
				#478928   armv8_pmuv3/exc_taken/
				for name in names:
					m = re.match(r'^\s*([0-9]+)\s+(' + name + ')\s*#?.*$', line.rstrip('\n'))
					if m:
						key = m.group(2)
						value = m.group(1)
						if not key in result:
							l = []
							l.append(float(value))
							result[key] = l
						else:
							result[key].append(float(value))

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
			#d = (result1[n] - result2[n]) / result2[n]
			d = result1[n] / result2[n]
			diff[n] = format_percentage(d)
		else:
			if not n in result1:
				print(n + " does exist in result1, skip")
			if not n in result2:
				print(n + " does exist in result2, skip")

	return diff

def get_diff(result, base, names, verbose):
	if not result or not base:
		print("testresult or testbase is empty, exit")
		sys.exit(2)

	(average_result, cv_result) = get_avg(result, names)
	(average_base, cv_base) = get_avg(base, names)

	if verbose:
		print("Original numbers:")
		print(average_base)
	#	print(cv_base)
		print(average_result)
	#	print(cv_result)
		print("")

	diff_result = diff(average_result, average_base)
	keys = diff_result.keys()
	keys.sort()

	max_len_of_key = 0
	for key in keys:
		if len(key) > max_len_of_key:
			max_len_of_key = len(key)

	max_len_of_base = 0
	for key in average_base:
		if len(str(int(average_base[key]))) > max_len_of_base:
			max_len_of_base = len(str(format(int(average_base[key]), ',')))

	max_len_of_result = 0
	for key in average_result:
		if len(str(int(average_result[key]))) > max_len_of_result:
			max_len_of_result = len(str(format(int(average_result[key]), ',')))

	print("Diff: result/base")
	print("%*s %*s %*s      %s   %s %s %s" % (max_len_of_key + 2, "testcases", max_len_of_base + 2, "base", max_len_of_result + 2, "result", "diff", "cv(base)", "cv(result)", "cv: Coefficient of Variation"))
	for key in keys:
		print("%*s %*s %*s  %s  %s   %s" % (max_len_of_key + 2, key, max_len_of_base + 2, format(int(average_base[key]), ','), max_len_of_result + 2, format(int(average_result[key]), ','), diff_result[key], cv_base[key], cv_result[key]))

def usage(argv):
	print("Usage:")
	print(argv[0] + ": --testresult /path/to/testresult --testbase /path/to/testbase")
	print("output the average and the diff of (avg(testresult) - arg(testbase))/avg(testbase)")
	print("--testresult: the path of test result. support multi paths")
	print("--testbase: the path of test base. support multi paths")

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hv", ["testresult=", "testbase="])
	except getopt.GetoptError as e:
		print("Argument error " + e.opt + ": " + e.msg)
		usage(argv)
		sys.exit(2)

	testresult = []
	testbase = []
	verbose=False
	for opt, arg in opts:
		if opt == "-h":
			usage(argv)
			sys.exit(2)
		elif opt == "-v":
			print("verbose")
			verbose=True
		elif opt == "--testresult":
			testresult.append(arg)
		elif opt == "--testbase":
			testbase.append(arg)

	if verbose:
		print("The test result:")
		print(testresult)
		print("The test base:")
		print(testbase)

	full_name = ["dTLB-load-misses", "iTLB-load-misses", "armv8_pmuv3/exc_taken/", "armv8_pmuv3/exc_taken/", "armv8_pmuv3/l2d_cache/", "L1-dcache-load-misses", "L1-dcache-loads", "L1-dcache-store-misses", "L1-dcache-stores"]
	get_diff(testresult, testbase, full_name, verbose)

if __name__ == "__main__":
	main(sys.argv[1:])

