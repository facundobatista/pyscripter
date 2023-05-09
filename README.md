# pyscripter

A tool that simulates typing and executing a Python script in a terminal window. 

It reads a script file and executes the code in real-time in a Python subprocess, typing out character-by-character both inputs and outputs retrieved from Python, giving the effect of an interactive interpreter usage.

The script file is just a sequence that one would type in a Python interactive interpreter, with the only detail/feature that if there is an empty line, that empty line will be reproduced **and** an extra pause will happen after that empty line (giving the effect of a separation between topics).

Note that after code blocks an empty line is also needed so that the interpreter knows that indentation is over, as usual.

Example of such a script that shows how to append and extend a list, and a weird interaction with the global variable:

```python
numbers = [1, 2, 3]
dir(numbers)
help(numbers.append)
# <script>: pause 3
numbers.append(45)
numbers

numbers.extend([1, 2])
numbers

def foo():
    numbers.append(23)

foo()
numbers
```

In this example, a long pause is explicitly requested after showing the help (so the watcher has time to read), and then natural pauses are included after showing the modified numbers list (but there is no extra pause between defining the function and executing it, that empty line is because indentation).


## Usage

`pyscripter.py <src_script>`

The only argument is the path to the script file to execute.


## Commands

Scripter supports the following commands, which should be prefixed with `# <script>:` (configurable):

- `pause <seconds>`: Pauses for the specified number of seconds.
- `python_exec <path>`: Specifies the path to the Python executable to use. This command should be used at the top of the script file.


## Tuning

Scripter can be configured with the following constants:

- `SCRIPTER_CMD_PREFIX`: The prefix that commands should be prefixed with. Default is `# <script>:`.
- `DELAY_LINE_PAUSE`: The pause duration in seconds after a separation block. Default is `2`.
- `DELAY_LINE_CR`: The pause duration in seconds after typing a line. Default is `0.2`.
- `DELAY_CHAR`: The pause duration in seconds between typing each character. Default is `0.1`.
- `DELAY_END`: The pause duration in seconds at the end of the script. Default is `3`.
