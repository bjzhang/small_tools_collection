#!/usr/bin/env python

import subprocess
import re
import sys

from pycparser import c_parser, c_ast
from cStringIO import StringIO

file_compat_ioctl_list = "/home/bamvor/works/source/small_tools_collection/abi_helper/compat_ioctl_list"

class __redirection__:
    def __init__(self):
        self.buff=''
        self.__console__=sys.stdout

    def write(self, output_stream):
        self.buff+=output_stream

    def to_console(self):
        sys.stdout=self.__console__
        print self.buff

    def to_file(self, file_path):
        f=open(file_path,'w')
        sys.stdout=f
        print self.buff
        f.close()

    def flush(self):
        self.buff=''

    def reset(self):
        sys.stdout=self.__console__

def cscope(cmd):
#    print cmd
    p = subprocess.Popen(["cscope", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    result = p.stdout.readlines()

    return result

#match: filename func_called line_number code
def cscope_parser(cscope_line):
    m = re.match(r'^([\w\-/]*\.[ch]) (\w+) ([0-9]+) (.+)$', cscope_line)
    if not m:
       return None
    filename = m.group(1)
    called = m.group(2)
    linenum = m.group(3)
    code = m.group(4)
#    print "cscope parser result: " + filename + ", " + called + ", " + linenum + ", " + code
    return (filename, called, linenum, code)

def get_variable_type(var_def):
    print var_def
    a = __redirection__()
    parser = c_parser.CParser()
    ast = parser.parse(var_def, filename='<none>')
    ast.show(a)
    print a.buff

def get_variable(calling_relation):
    (filename, func, called, linenum, var) = calling_relation

    m = re.match(r'^(&?)(\w+)([.->]+(.*))?', var)
    base_var = m.group(2)

    cscope_var = cscope("-f cscope.out -d -l -L -0" + base_var)
    cscope_var = [line.strip() for line in cscope_var]
    func_var = [x for i, x in enumerate(cscope_var) if re.search(func, x)]
    element = cscope_parser(func_var[0])
    if element and element[3]:
        var_definition = element[3]
        get_variable_type(var_definition)
        return (filename, func, called, linenum, var, var_definition)
    else:
        return None

def get_called_user_func(func, calleds_user, max_tries):
#    cscope_calleds = cscope("-f /home/bamvor/works/source/kernel/linux/cscope.out -d -l -L -2" + func)
    cscope_calleds = cscope("-f cscope.out -d -l -L -2" + func)
    cscope_calleds = [line.strip() for line in cscope_calleds]
    calleds = []
    for line in cscope_calleds:
        ret = True
        if ret:
            element = cscope_parser(line)
            if element and element[1]:
                called = element[1]
                if called == 'copy_from_user' or called == 'get_user':
                    code = element[3]
                    m = re.match(r'^.*' + called + '\(([a-zA-Z_0-9\-&>.()\[\]]+),.*$', code)
                    if m and m.group(0) and m.group(1):
                        calling_relation = (element[0], func, element[1], element[2], m.group(1))
#                        print calling_relation
                        calling_relation = get_variable(calling_relation)
                        calleds_user.append(calling_relation);
                    else:
                        print "####Could not handle <" + code + ">####"
                        sys.exit()

                    return
                elif called != 'pr_info':
                    if max_tries - 1 > 0:
                        get_called_user_func(called, calleds_user, max_tries - 1)
#                    else:
#                        print "max tries encounter. return"
            else:
                print "parser func in line:< " + line + "> fail. exit!!!"
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

compat_ioctl_func = ['binder_ioctl']
compat_ioctl_func_no_found = []
for func in compat_ioctl_func:
    calleds_user_func = []
    get_called_user_func(func, calleds_user_func, 3)
    if calleds_user_func:
        print func + ": "
        print calleds_user_func
    else:
        compat_ioctl_func_no_found.append(func);

print "copy_from_user or get_user is not found in the following compat_ioctl functions"
