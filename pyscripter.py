#!/usr/bin/python3

import random
import select
import subprocess
import sys
import time
import termios
import tty
from collections import namedtuple, deque

# all commands need to start with this
SCRIPTER_CMD_PREFIX = "# <pyscript>:"

# this is a big pause for separating the chunks, to ease the video cutting
DELAY_LINE_PAUSE = 2
# this is for writing cadence
DELAY_CHAR = .1
# before finishing everything (so the user prompt doesn't appear fast)
DELAY_END = 3

# the different prompts in the Python interactive interpreter; after the >>> we have a
# small delay that reflects the user waiting for something to finish before writing again,
# bu after the ... we don't wait as the input had not really finished
PROMPTS = [
    ([b'>', b'>', b'>', b' '], .5),
    ([b'.', b'.', b'.', b' '], 0),
]

# keys that will be used to pause/unpause
PAUSE_KEYS = (" ", "p", "\r", "\n")

Command = namedtuple('Command', 'func args')


def wait_for_prompt(proc):
    """Waits for the Python interpreter to offer any of the prompts."""
    # write *bytes* directly here (can't decode one byte at a time!)
    stdout_buffer = sys.stdout.buffer

    sequence = deque(maxlen=4)
    while True:
        byte = proc.stdout.read(1)
        stdout_buffer.write(byte)
        stdout_buffer.flush()
        sequence.append(byte)
        lseq = list(sequence)
        for prompt, delay in PROMPTS:
            if lseq == prompt:
                time.sleep(delay)
                return


def maybe_pause():
    """Maybe block main process if user paused, until unpauses.

    Note that reading from stdin is always blocking, that's why first time we ask
    first if something is there. Then in the pause loop it's not needed, as
    we *want* to block.
    """
    ready_to_read, _, _ = select.select([sys.stdin], [], [], 0)
    if ready_to_read != [sys.stdin]:
        return
    ch = sys.stdin.read(1)

    if ch in PAUSE_KEYS:
        while True:
            ch = sys.stdin.read(1)
            if ch in PAUSE_KEYS:
                break


def main(filepath):
    """Main entry point."""
    python_exec = "python3"

    # get all the lines
    script_lines = []
    with open(filepath, 'rt', encoding='utf8') as fh:
        for idx, line in enumerate(fh, 1):
            if line.startswith("##"):
                continue

            if not line.startswith(SCRIPTER_CMD_PREFIX):
                script_lines.append(line.rstrip(' '))
                continue

            # command line!
            line = line[len(SCRIPTER_CMD_PREFIX):].strip()
            command, *options = line.split()
            if command == 'pause':
                (delay,) = options
                script_lines.append(Command(func=time.sleep, args=(float(delay),)))
            elif command == 'start':
                script_lines.clear()
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

    proc = subprocess.Popen(
        [python_exec, "-u", "-i"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    wait_for_prompt(proc)

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
            maybe_pause()

        # send the line to Python all at once for real processing
        proc.stdin.write(line.encode('utf8'))
        proc.stdin.flush()

        wait_for_prompt(proc)
        maybe_pause()

    time.sleep(DELAY_END)
    print()


if len(sys.argv) != 2:
    print("USAGE: scripter.py <src_script>")
    exit()

# run main wrapped around setting stdin to not wait newline to send characters
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
try:
    tty.setcbreak(fd)
    main(sys.argv[1])
except KeyboardInterrupt:
    print("\nInterrupted by user")
    exit(1)
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
