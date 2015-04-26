#!/usr/bin/env python

import datetime
import io
import logging
import os
import signal
import subprocess
import collections

import time
import sys

env = dict(os.environ)
logger = logging.getLogger()

def _io_open(command, working_dir=None):
    logger.debug("In _io_open.")

    buffer_size = 1

    if isinstance(command, list):
        logger.debug("Command provided is a list.")
        command_line = ' '.join(command)
    else:
        logger.debug("Command provided is a simple string.")
        command_line = command

    process = None

    if working_dir is None:
        logging.debug("No working directory specified for subprocess.")
        process = subprocess.Popen(command_line, shell=True,
                                   preexec_fn=preexec_function,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   bufsize=buffer_size)
    else:
        process = subprocess.Popen(command_line, shell=True,
                                   preexec_fn=preexec_function,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   bufsize=buffer_size, cwd=working_dir)

    stdouts = io.open(process.stdout.fileno())
    stderrs = io.open(process.stderr.fileno())

    for stdout_line in stdouts:
        yield stdout_line.rstrip('\n')

    stderr = "".join(stderrs)

    exit_value = process.wait()
    logger.debug("Exit value: %s" % str(exit_value))

    if not process.stderr.closed:
        process.stderr.close()

    if not process.stdout.closed:
        process.stdout.close()

    yield "IOOPENEXIT: " + str(exit_value)
    yield "IOOPENSTDERR: " + stderr


def run_command_streaming_stdout(command, working_dir=None):
    logger.debug("In run_command_streaming_stdout.")

    lines = []

    for line in _io_open(command, working_dir=working_dir):
        if line.startswith("IOOPENEXIT:") or line.startswith("IOOPENSTDERR:"):
            pass
        else:
            print(line)
            sys.stdout.flush()

        lines.append(line)

    # Need to retrieve the exit value and stderr which _io_open also yields
    # but have to do it in the correct order. First we strip out the marker
    # that flags the data as the executables STDERR.
    stderr = lines.pop()
    stderr = stderr.lstrip("IOOPEN_STDERR: ")

    # Then we strip out the marker that flags this as the executable's exit
    # value and convert back to an integer
    exit_value = lines.pop()
    exit_value = int( exit_value.lstrip("IOOPENEXIT: "))

    stdout = "\n".join(lines)

    return (exit_value, stdout, stderr)

def run_sudo_command_streaming_stdout(command, log_file, working_dir=None, target_user=None):
    logger.debug("In run_sudo_command_streaming_stdout.")

    cmd = [ '/usr/bin/sudo',
            '-E',
          ]

    if target_user is not None:
        cmd.extend(['-u', target_user])

    for command_arg in command:
        cmd.append(command_arg)

    lines = []

    for line in _io_open(cmd, working_dir=None):
        if line.startswith("IOOPENEXIT:") or line.startswith("IOOPENSTDERR:"):
            pass
        else:
            print(line)

        lines.append(line)

    # Need to retrieve the exit value and stderr which _io_open also yields
    # but have to do it in the correct order. First we strip out the marker
    # that flags the data as the executables STDERR.
    stderr = lines.pop()
    stderr = stderr.lstrip("IOOPEN_STDERR: ")

    # Then we strip out the marker that flags this as the executable's exit
    # value and convert back to an integer
    exit_value = lines.pop()
    exit_value = int( exit_value.lstrip("IOOPENEXIT: "))

    stdout = "\n".join(lines)

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")

    temp = open(log_file, 'a');
    temp.write('%s  %s\n%s\n' % (timestamp, stdout, stderr))
    temp.close();

    return (exit_value, stdout, stderr)


def preexec_function():
    # The setpgrp() call prevents a SIGINT from being propagated
    # to child processes.
    os.setpgrp()
    # Ignore the SIGINT signal by setting the handler to the standard
    # signal handler SIG_IG.
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_sudo_command(command, log_file, working_dir=None, target_user=None):
    logger.debug("In run_sudo_command.")

    cmd = [ '/usr/bin/sudo',
            '-E',
          ]

    if target_user is not None:
        cmd.extend(['-u', target_user])

    for command_arg in command:
        cmd.append(command_arg)

    pipe = None

    if working_dir is None:
        pipe = subprocess.Popen(' '.join(cmd), stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                preexec_fn=preexec_function,
                                env=env, shell=True)
    else:
        pipe = subprocess.Popen(' '.join(cmd), stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                preexec_fn=preexec_function,
                                env=env, shell=True, cwd=working_dir)

    stdoutData, stderrData = pipe.communicate()

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")

    temp = open(log_file, 'a');
    temp.write('%s  %s\n%s\n' % (timestamp, stdoutData, stderrData))
    temp.close();

    exitCode = pipe.wait()

    return (exitCode, stdoutData, stderrData)

def run_command(command, working_dir=None):
    logger.debug("In run_command.")

    cmd = []
    for command_arg in command:
        cmd.append(command_arg)

    logger.debug(cmd)

    if working_dir is None:
        logger.debug("No working directory provided for where to invoke command from.")
        pipe = subprocess.Popen(' '.join(cmd), stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                                preexec_fn=preexec_function,
                                shell=True)
    else:
        logger.debug("Invoking command from %s." % working_dir)
        pipe = subprocess.Popen(' '.join(cmd), stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                                preexec_fn=preexec_function,
                                shell=True, cwd=working_dir)

    stdoutData, stderrData = pipe.communicate()

    logger.debug("Waiting for the command to complete.")
    exitCode = pipe.wait()

    return (exitCode, stdoutData, stderrData)
