#!/usr/bin/env python

import subprocess
import re

file_compat_ioctl_list = "/home/bamvor/works/source/small_tools_collection/abi_helper/compat_ioctl_list"

def cscope(cmd):
#    print cmd
    p = subprocess.Popen(["cscope", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    result = p.stdout.readlines()

    return result

def get_called_user_func(func, calleds_user, max_tries):
#    cscope_calleds = cscope("-f /home/bamvor/works/source/kernel/linux/cscope.out -d -l -L -2" + func)
    cscope_calleds = cscope("-f cscope.out -d -l -L -2" + func)
    cscope_calleds = [line.strip() for line in cscope_calleds]
    calleds = []
    for line in cscope_calleds:
        ret = True
        if ret:
#           match: filename func_called line_number code
            m = re.match(r'^([a-zA-Z0-9_/]*\.[ch]) ([a-zA-Z0-9_]+) ([0-9]+) (.+)$', line)
            if not m:
                continue
            filename = m.group(1)
            called = m.group(2)
            linenum = m.group(3)
            code = m.group(4)
            if called:
                if called == 'copy_from_user' or called == 'get_user':
                    print "code is "
                    print code
                    print "code end"
                    variable = re.match(r'^.*' + called + '\(([a-zA-Z_0-9\-&>.()\[\]]+),.*$', code).group(1)
                    calling_relation = (filename, func, called, linenum, variable)
                    calleds_user.append(calling_relation);
                    return
                elif called != 'pr_info':
                    if max_tries - 1 > 0:
                        get_called_user_func(called, calleds_user, max_tries - 1)
#                    else:
#                        print "max tries encounter. return"
            else:
                print "parser func fail. exit!!!"
                sys.exit()

compat_ioctl_list = [line.strip() for line in open(file_compat_ioctl_list)]
compat_ioctl_func = []

for l in compat_ioctl_list:
    want = False
    if re.search('^arch', l):
        if re.search('^arch\/arm64', l):
            want = True
    elif re.search('^Documentation', l):
        pass
    else:
        want = True

    if want:
        func = re.sub(r'^.*:(.*)$', r'\1', l)
        compat_ioctl_func.append(func)

#compat_ioctl_func = ['binder_ioctl']
compat_ioctl_func_no_found = []
for func in compat_ioctl_func:
#    print func
    calleds_user_func = []
    get_called_user_func(func, calleds_user_func, 3)
    if calleds_user_func:
        print func + ": "
        print calleds_user_func
    else:
        compat_ioctl_func_no_found.append(func);

print "copy_from_user or get_user is not found in the following compat_ioctl functions"
print compat_ioctl_func_no_found
