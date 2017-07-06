#!/usr/bin/env python

"""
Usage - 

%(scriptName)s [--debug] [--p pid1,pid2,...]

--p pid1,pid2,... = Show output only for the specified pids.  If --p not specified, output for all pids is displayed.
--debug = Enable DEBUG output.

"""

import os, sys, re
import getopt
import logging

scriptName = os.path.basename(os.path.realpath(__file__))
scriptDir = os.path.dirname(os.path.realpath(__file__))

sys.path.append(scriptDir+'/lib')

from run_command import run_command
from run_command import xrange
from logging_wrappers import logging_setup, debug_option
from columnize_output import columnize_output

#=============================================================

def usage(exit_or_return='exit'):
    print(__doc__ % {'scriptName': scriptName, })
    if exit_or_return == 'exit':
        sys.exit(1)
    else:
        return

#=============================================================

output_string = []
output_list   = []

global ps_list_sorted
ps_list_sorted = []

def walk_ps_list(ppid, indent):
    for index in range(len(ps_list_sorted)):
        if len(ps_list_sorted[index]) > 0 and ppid == ps_list_sorted[index][1]:
            # output_string.append(str(indent + str(ps_list_sorted[index][0]) + "   " + str(ps_list_sorted[index][1]) + '   ' + ps_list_sorted[index][2]))
            output_string.append(str(indent + str(ps_list_sorted[index][0]) + "   " + ps_list_sorted[index][2]))
            output_list.append([indent + str(ps_list_sorted[index][0]), ps_list_sorted[index][2]])
            next_ppid = ps_list_sorted[index][0]
            ps_list_sorted[index] = []
            walk_ps_list(next_ppid, indent + '---')

#=============================================================


if __name__ == '__main__':

    debug = debug_option()

    log = logging_setup(scriptName + '.log', logging.ERROR, 'PS:')

    # if len(sys.argv) == 1:
    #     # log.error("Not enough runstring options.")
    #     print("Not enough runstring options.")
    #     usage()

    pid_csv_list = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["p=", "list=", "of=", "debug", "columnize", "h", "help"])
    except:
        log.error("Unrecognized runstring option.")
        usage()

    for opt, arg in opts:
        if opt == "--p":
            pid_csv_list = arg
        elif opt == "--h" or opt == "--help":
            usage()
        elif opt == "--of":
            of_option = arg
        elif opt == "--columnize":
            columnize = 'yes'
        elif opt == "--debug":
            setLoggingLevel(logging.DEBUG)
        else:
            log.error("Runstring option error.")
            usage()

    # rc, output, error = run_command("ps -ef")
    rc, output, error = run_command("procps -wwFAH")
    # results = output.decode() + error.decode()
    results = output + error
    if rc != 0:
        log.error("run_command() error = " + results)
        sys.exit(1)
    # print("results = " + results + ". end results")

    # Linux format:
    # found = re.search('^([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +(.+)$', line)
    # Cygwin ps -ef:
    # UID     PID    PPID  TTY        STIME COMMAND
    #  mi   11372   11640 pty1     16:21:36 /usr/bin/vim
    
    # print(186, "     UID     PID    PPID  TTY        STIME COMMAND")
    # print(186, "          0         0         0         0         ")
    # print(186, "01234567890123456789012345678901234567890123456789")
 
    PID_start_position = -1
    PID_end_position = -1
    PPID_start_position = -1
    PPID_end_position = -1
    COMMAND_start_position = -1
    # results_list = results.split(b'\n')
    results_list = results.split('\n')
    for line in results_list:
        # print(116, line)
        if 'PID' in line and 'PPID' in line:
            collecting_word = False
            word = ''
            column_start = 0
            for index in range(len(line)):
                # print(98, 'len(line) =', len(line))
                # print(98, 'line['+str(index)+'] =', line[index])
                # print(98, 'column_start =', column_start)
                # print(98, 'collecting_word =', collecting_word)
                # print(99, 'word =', word)
                if collecting_word == False:
                    if line[index] == ' ':
                        continue
                    else:
                        collecting_word = True
                        word += line[index]
                else:
                    if line[index] != ' ':
                        word += line[index]

                    if word == 'PID':
                        # print(110, 'PID match')
                        PID_start_position = column_start
                        PID_end_position = index - 1
                    elif word == 'PPID':
                        # print(114, 'PPID match')
                        PPID_start_position = column_start
                        PPID_end_position = index - 1
                    elif word == 'COMMAND' or word == 'CMD':
                        # print(119, 'COMMAND match')
                        COMMAND_start_position = column_start

                    if line[index] == ' ':
                        column_start = index
                        collecting_word = False
                        word = ''
            break

    if PID_start_position == -1:
        log.error("Missing PID header line in ps output.")
        sys.exit(1)
    # print(106, PID_start_position)
    # print(124, PID_end_position)
    PID_length = PID_end_position - PID_start_position + 1
    # print(126, PID_length)

    if PPID_start_position == -1:
        log.error("Missing PPID header line in ps output.")
        sys.exit(1)
    # print(111, PPID_start_position)
    # print(130, PPID_end_position)
    PPID_length = PPID_end_position - PPID_start_position + 1
    # print(134, PPID_length)

    if COMMAND_start_position == -1:
        log.error("Missing COMMAND header line in ps output.")
        sys.exit(1)
    # print(116, COMMAND_start_position)

    ps_list = []
    for line in results_list:
        if line == '':
            continue
        if 'PID' in line and 'PPID' in line:
            continue
        # print(128, line)

        # print(186, "     UID     PID    PPID  TTY        STIME COMMAND")
        # print(186, "          0         0         0         0         ")
        # print(186, "01234567890123456789012345678901234567890123456789")
        # print(186, line)

        search_string = '^'+'.'*PID_start_position+'('+'.'*PID_length+')'
        # print(138, search_string)
        found = re.search(search_string, line)
        PID = int(found.group(1))

        search_string = '^'+'.'*PPID_start_position+'('+'.'*PPID_length+')'
        # print(151, search_string)
        found = re.search(search_string, line)
        PPID = int(found.group(1))

        search_string = '^'+'.'*COMMAND_start_position+'(.+)$'
        # print(151, search_string)
        found = re.search(search_string, line)
        CMD = found.group(1)

        # UID = found.group(1)
        # PID = int(found.group(PID_position))
        # PPID = int(found.group(PPID_position))
        # C = found.group(4)
        # STIME = found.group(5)
        # TTY = found.group(6)
        # TIME = found.group(7)
        # CMD = found.group(COMMAND_position)

        ps_list.append([PID, PPID, CMD])

    if pid_csv_list == '':
        ps_list.append([1, -1, "init"])
    ps_list_sorted = sorted (ps_list, key=lambda x: int(x[1]))
    # for line in ps_list_sorted:
    #     print(line)
    indent = ''
    if pid_csv_list != '':
        ps_list_sorted_save = ps_list_sorted
        for pid in pid_csv_list.split(','):
            output_string.append("")
            output_string.append("------------------------------------------")
            output_string.append("pid tree to search for = " + pid)
            output_string.append("")
            found = False
            for index in range(len(ps_list_sorted)):
                if int(pid) == ps_list_sorted[index][0]:
                    output_string.append(str(indent + str(ps_list_sorted[index][0]) + "   " + str(ps_list_sorted[index][1]) + '   ' + ps_list_sorted[index][2]))
                    output_list.append([str(ps_list_sorted[index][0]), ps_list_sorted[index][2]])
                    found = True
                    break
            if found == False:
                print(("ERROR: pid " + pid + " not found in our sorted list."))
            walk_ps_list(int(pid), indent + '---')
            ps_list_sorted = ps_list_sorted_save
    else:
        walk_ps_list(ps_list_sorted[0][1], indent)

    # for row in output_string:
    #    print(row)

    rc, output_columnized = columnize_output(output_list, justify_cols='L,L')
    for row in output_columnized:
        print(row)


