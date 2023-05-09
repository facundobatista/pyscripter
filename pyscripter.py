#!/usr/bin/python3

import random
import subprocess
import sys
import time
from collections import namedtuple

# all commands need to start with this
SCRIPTER_CMD_PREFIX = "# <script>:"

# this is a big pause for separating the chunks, to ease the video cutting
DELAY_LINE_PAUSE = 2
# need this delay for Python to actually show the results
DELAY_LINE_CR = .2
# this is for writing cadence
DELAY_CHAR = .1
# before finishing everything (so the user prompt doesn't appear fast)
DELAY_END = 3


Command = namedtuple('Command', 'func args')


def main(filepath):
    """Main entry point."""
    python_exec = "python3"

    # get all the lines
    script_lines = []
    with open(filepath, 'rt', encoding='utf8') as fh:
        for idx, line in enumerate(fh, 1):
            if not line.startswith(SCRIPTER_CMD_PREFIX):
                script_lines.append(line.rstrip(' '))
                continue

            # command line!
            line = line[len(SCRIPTER_CMD_PREFIX):].strip()
            command, *options = line.split()
            if command == 'pause':
                (delay,) = options
                script_lines.append(Command(func=time.sleep, args=(float(delay),)))
            elif command == "python_exec":
                # this line is ignored but affect "config"
                if idx != 1:
                    print("ERROR: 'python_exec' command found NOT in the top of the file")
                    exit()
                (path,) = options
                python_exec = path
            else:
                print("ERROR: bad command found in the script (l.{}): {!r}".format(idx, line))
                exit()

    # post-process to add a delay after a separation block (which is any empty line that
    # is not really used to "end an indented block")
    #
    post_proc = []
    state = None  # also: "block", "closing", "separation"
    for line in script_lines:
        post_proc.append(line)
        if isinstance(line, Command):
            continue

        is_empty = not line.strip()
        is_indented = line.startswith(" ")

        if state is None:
            if is_empty:
                state = 'separation'
            elif is_indented:
                state = 'block'
            else:
                state = None
        elif state == 'block':
            if is_empty:
                state = 'closing'
            elif is_indented:
                state = 'block'
            else:
                state = 'block'
        elif state == 'closing':
            if is_empty:
                state = 'separation'
            elif is_indented:
                raise ValueError("Got indented when in closing")
            else:
                state = None
        elif state == 'separation':
            if is_empty:
                state = 'separation'
            elif is_indented:
                raise ValueError("Got indented when in separation")
            else:
                post_proc.insert(-1, Command(func=time.sleep, args=(DELAY_LINE_PAUSE,)))
                state = None
        else:
            raise ValueError("Bad state")
    script_lines = post_proc

    # clear screen and set cursor at the top left
    print('\x1b[2J\x1b[H', end='', flush=True)

    proc = subprocess.Popen([python_exec, "-i"], stdin=subprocess.PIPE)
    time.sleep(DELAY_LINE_PAUSE)  # start with a pause to leave proper time for Python to bootstrap

    for line in script_lines:
        # check if it's a command result
        if isinstance(line, Command):
            line.func(*line.args)
            continue

        # show the line with a per-char cadence
        for c in line:
            sys.stdout.write(c)
            sys.stdout.flush()
            fuzzyness = 1 + (random.random() - 0.5)  # +/- 50%
            time.sleep(DELAY_CHAR * fuzzyness)

        # send the line to Python all at once for real processing
        proc.stdin.write(line.encode('utf8'))
        proc.stdin.flush()
        time.sleep(DELAY_LINE_CR)

    time.sleep(DELAY_END)


if len(sys.argv) != 2:
    print("USAGE: scripter.py <src_script>")
    exit()
main(sys.argv[1])
