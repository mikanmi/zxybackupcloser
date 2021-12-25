#!/usr/bin/env python3

# Copyright (c) 2021 Patineboot. All rights reserved.
# ZxyBackupCloser is licensed under BSD 2-Clause License.

# BSD 2-Clause License
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from typing import Final

import os
import time
import subprocess
from threading import Thread

READSIZE: Final[int] = 64 * 1024
LOGGER = None


def multi_pipe(inputstream, outputstreams):
    LOGGER.debug(f"STR: {inputstream}, {outputstreams}")

    def run(istream, ostreams):

        readbuffer = bytearray(READSIZE)

        while True:
            size = istream.readinto(readbuffer)
            if size == 0:
                istream.close()
                [o.close() for o in ostreams]
                break
            readdata = readbuffer[0:size]
            for o in ostreams:
                wsize = o.write(readdata)
                if size != wsize:
                    LOGGER.error(f"actual write size {wsize}, attempt write size {size}.")
                    raise IOError(f"actual write size {wsize}, attempt write size {size}.")

            # for thread switching
            time.sleep(0.0001)

    thread = Thread(target=run, args=(inputstream, outputstreams))
    thread.start()

    LOGGER.debug(f"END: {thread}")
    return thread


def line_pipe(inputstream, handler):
    LOGGER.debug(f"STR: {inputstream}, {handler}")

    def run(inputstream, handler):

        while True:
            line = inputstream.readline()
            size = len(line)
            if size == 0:
                inputstream.close()
                break

            handler(line.decode())

    thread = Thread(target=run, args=(inputstream, handler))
    thread.start()

    LOGGER.debug(f"END: {thread}")
    return thread


class Command:

    @classmethod
    def initialize(cls, logger, dryrun):
        global LOGGER
        LOGGER = logger
        cls.__dryrun = dryrun

    def __init__(self, commandline):
        """Construct Command instance,
        Args:
            commandline: A shell command with some options if existed.
        """
        LOGGER.debug(f"STR: {commandline}")

        self.__commandline: str = commandline
        self.__subcommands: list[Command] = []
        self.__handle_stderr: bool = True

        LOGGER.debug(f"END")

    def add_subcommand(self, comand):
        """Add a command piped with the first command.
        Args: A command with which Command instance pipes.
        """
        LOGGER.debug(f"STR: {comand}")

        self.__subcommands.append(comand)

        LOGGER.debug(f"END")

    def __print_command(self, tag, shift):
        LOGGER.info(f"{tag}:{shift}{self.__commandline}")
        shift = shift.replace("+", " ") + " + "
        for subcommand in self.__subcommands:
            subcommand.__print_command(tag, shift)

    def execute(self, stdout_callback=None, stderr_callback=None, stdin_input=None, always=False):
        """Run the command with bloking call.
        Args:
            stdin_input: Provide stdin an inputstream to input incremental. None if no input to the command.
            stdout_callback: Call print_out with a text reading from stdout.
                            None if getting stdout on retrun value.
            stderr_callback: Call print_err with a text reading from stderr.
                            None if getting stderr on retrun value.
        Returns:
            int: returncode.
        """
        LOGGER.debug(f"STR: {stdout_callback}, {stderr_callback}, {stdin_input}, {always}")

        dryrun = self.__dryrun and not always

        tag = "PRT" if dryrun else "CMD"
        shift = " "
        self.__print_command(tag, shift)

        if self.__dryrun and not always:
            return "Under Dryrun."

        whole_stdout = []

        def default_stdout(line):
            whole_stdout.append(line)

        def default_stderr(line):
            output = line.rstrip(os.linesep)
            LOGGER.error(output)

        stdout_handler = default_stdout if stdout_callback is None else stdout_callback
        stderr_handler = default_stderr if stderr_callback is None else stderr_callback

        processes = []
        threads = []
        pro = self.__start(processes, threads, stdout_handler, stderr_handler)

        # interrupt and handle standard io, e.g., log, pipe, etc
        if stdin_input is not None:
            thread = multi_pipe(stdin_input, [pro.stdin, ])
            thread.join()
            pro.stdin.close()

        [thread.join() for thread in threads]

        for process in processes:
            process.wait()
            if process.returncode != 0:
                LOGGER.error(f"command: {process.args}")
                LOGGER.error(f"returncode: {process.returncode}")
                process.check_returncode()

        wholestdout = f"".join(whole_stdout)
        LOGGER.debug(f"END: omit standard output to print.")
        return wholestdout

    def __start(self, processes, threads, stdout_callback, stderr_callback):

        simple = len(self.__subcommands) == 0

        perr = subprocess.PIPE
        if not self.__handle_stderr:
            perr = None

        split_cmd = self.__commandline.split()
        process = subprocess.Popen(
            split_cmd,
            bufsize=READSIZE,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=perr)
        processes.append(process)

        # start handling stderr
        if self.__handle_stderr:
            threads.append(line_pipe(process.stderr, stderr_callback))

        if simple:
            # start handling stdout of the final command.
            threads.append(line_pipe(process.stdout, stdout_callback))
            return process

        # start binding stdout to stdin of the sub commands.
        stdout_list = []
        for subcommand in self.__subcommands:
            bind_process = subcommand.__start(processes, threads, stdout_callback, stderr_callback)
            stdout_list.append(bind_process.stdin)

        if len(stdout_list) > 0:
            # copy one stdout to multiple stdin of sub commands.
            threads.append(multi_pipe(process.stdout, stdout_list))

        return process

    def handle_stderr(self, check):
        self.__handle_stderr = check


if __name__ == "__main__":
    print("CommandOption is an Import Module.")
