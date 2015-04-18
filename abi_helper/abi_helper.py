#!/usr/bin/env python

import subprocess
import re
import sys

from pycparser import c_parser, c_ast
from cStringIO import StringIO

file_compat_ioctl_list = "/home/bamvor/works/source/small_tools_collection/abi_helper/compat_ioctl_list"

class __redirection__:
    def __init__(self):
        self.buff=[]
        self.__console__=sys.stdout
        self.current_line = ''

    def write(self, output_stream):
        if output_stream == '\n':
            self.buff.append(self.current_line)
            self.current_line = ''
        else:
            self.current_line += output_stream

def cscope(cmd):
#    print cmd
    p = subprocess.Popen(["cscope", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    result = p.stdout.readlines()

    return result

#match: filename func_called line_number code
def cscope_parser(cscope_line):
    m = re.match(r'^([\w\-/]*\.[ch]) (<?\w+>?) ([0-9]+) (.+)$', cscope_line)
    if not m:
       return None
    filename = m.group(1)
    called = m.group(2)
    linenum = m.group(3)
    code = m.group(4)
#    print "cscope parser result: " + filename + ", " + called + ", " + linenum + ", " + code
    return (filename, called, linenum, code)

def get_variable_type(var_name, var_def):
#    print var_def
    var_root_name = None
    var_root_type_name = None
    var_root_type = None
    a = __redirection__()
    parser = c_parser.CParser()
    var_def = re.sub(r'\s__user\s', '', var_def)
    try:
        ast = parser.parse(var_def, filename='<none>')
    except:
        return None

    ast.show(a)
#    print a.buff
    for line in a.buff:
        #'    TypeDecl: bwr, []', '
        m = re.match(r'^\s*TypeDecl: (\w*),.*$', line)
        if m and m.group(1) and m.group(1) == var_name:
            var_root_name = m.group(1)
#            print "var_root_name: <" + var_root_name + ">"
            continue

        if var_root_name:
            #'      Struct: binder_write_read'
            m = re.match(r'^\s*(\w*): (\w*)$', line)
            if m and m.group(2):
                var_root_type_name = m.group(1)
                var_root_type = m.group(2)
                print "    1: var_root_type_name: <" + var_root_type_name + ">, var_root_type: <" + var_root_type + ">"
                break

            #"        IdentifierType: ['char']"
            m = re.match(r'''^\s*IdentifierType: \[['"](\w*)['"]\]$''', line)
            if  m and m.group(1):
#                print "#########"
                var_root_type_name = ''
                var_root_type = m.group(1)
                print "    2: var_root_type_name: <" + var_root_type_name + ">, var_root_type: <" + var_root_type + ">"
                break

            #"      IdentifierType: ['unsigned', 'int']",
            #FIXME: may this varible is not the var found before
            #       get_variable, But it is ok for now. Because
            #       all the variable at the same line should be
            #       the SAME root type
            m = re.match(r'''^\s*IdentifierType: \[['"](\w*)['"], ['"](\w*)['"]\]$''', line)
            if  m and m.group(2):
                var_root_type_name = ''
                var_root_type = m.group(1) + ' ' + m.group(2)
                print "    3: var_root_type_name: <" + var_root_type_name + ">, var_root_type: <" + var_root_type + ">"
                break
            else:
                return None

    if var_root_name:
        print "    var is: " + var_root_type_name + ", " + var_root_type + ", " + var_root_name
    return (var_root_type_name, var_root_type, var_root_name)

def get_variable(calling_relation, hand):
    var_definition_global = None
    print calling_relation
    (filename, func, called, linenum, var) = calling_relation

    m = re.match(r'^(&?)(\w+)([.->]+(.*))?', var)
    base_var = m.group(2)

    cscope_var = cscope("-f cscope.out -d -l -L -0" + base_var)
    cscope_var = [line.strip() for line in cscope_var]
#    func_var = [x for i, x in enumerate(cscope_var) if re.search(func, x)]
#    element = cscope_parser(func_var[0])
#    element = cscope_parser(func_var[0])
    element = ()
    func_var = []
    for x in cscope_var:
        element = cscope_parser(x)
        if element and element[1] == '<global>' and (not var_definition_global):
            print "  Found the global definition line in line <" + x + ">"
            var_definition_global = element[3]
        elif element and element[1] == func:
            print "  Found the first line in function<" + func + "> in line <" + x + ">"
            var_definition = element[3]
            break

    var_root = None
    if var_definition:
        var_root = get_variable_type(base_var, var_definition)
        if not var_root:
            m = re.match(r'^(\w+) .*$', var_definition)
            if m and m.group(1):
                predefined = m.group(1)
                var_root = get_variable_type(base_var, "typedef void* " + predefined + ";" + var_definition)

        if not var_root:
            var_definition_hand = var_definition + ";"
            print "  var_definition_hand: " + var_definition_hand
            var_root = get_variable_type(base_var, var_definition_hand)
            if var_root:
                hand.write(var_definition + "\n")
                hand.write(var_definition_hand+ "\n")
                hand.flush()

        if var_root:
            return (filename, func, called, linenum, var, var_definition, var_root)

#    if var_definition_global and (not var_root):
#        var_root = get_variable_type(base_var, var_definition)
#        if not var_root:
#            m = re.match(r'^(\w+) .*$', var_definition)
#            predefined = m.group(1)
#            var_root = get_variable_type(base_var, "typedef void* " + predefined + ";" + var_definition)
#
#        if var_root:
#            return (filename, func, called, linenum, var, var_definition, var_root)

    if not var_root:
        print "  Parse <" + var_definition + "> failed"
        if var_definition_global:
            print '  Please input the correct type, leave empty for using the following global definition: <' + var_definition_global + '>: '
            try:
                var_definition_hand = input('  : ')
            except:
                var_definition_hand = var_definition_global
        else:
            var_definition_hand = input('  Please input the correct type:')

        var_root = get_variable_type(base_var, var_definition_hand)
        hand.write(var_definition + "\n")
        hand.write(var_definition_hand+ "\n")
        hand.flush()
        return (filename, func, called, linenum, var, var_definition, var_root)

    return None

def get_called_user_func(func, calleds_user, max_tries, hand):
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
                        calling_relation = get_variable(calling_relation, hand)
                        calleds_user.append(calling_relation);
                    else:
                        print "####Could not handle <" + code + ">####"
                        sys.exit()

                    return
                elif called != 'pr_info':
                    if max_tries - 1 > 0:
                        get_called_user_func(called, calleds_user, max_tries - 1, hand)
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

#compat_ioctl_func = ['binder_ioctl']
compat_ioctl_func_no_found = []
nt_found = open('compat_ioctl_func_no_found.txt', 'a')
hand = open('compat_ioctl_func_by_hand.txt', 'a')
i = 0
start = False
for func in compat_ioctl_func:
#    if func == "compat_raw_ioctl":
#        start = True
#
#    if not start:
#        i+=1
#        continue

    print "###########################################################"
    calleds_user_func = []
    get_called_user_func(func, calleds_user_func, 3, hand)
    if calleds_user_func:
        print "<" + str(i) + "> " + func + ": "
        print calleds_user_func
    else:
        nt_found.write(func + "\n")
        nt_found.flush()

    i+=1

hand.close()
nt_found.close()

print "copy_from_user or get_user is not found in the following compat_ioctl functions"
print compat_ioctl_func_no_found

