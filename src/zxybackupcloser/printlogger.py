#!/usr/bin/env python3

# Copyright (c) 2021 Patineboot. All rights reserved.
# ZxyBackupCloser is licensed under BSD 2-Clause License.

from typing import Final

import sys
import logging
from logging.handlers import RotatingFileHandler

LOGGER_LOG_LEVEL: Final[int] = logging.INFO


class PrintLogger(logging.getLoggerClass()):
    """PrintLogger is a logger class.
    """

    def __init__(self, name):
        super().__init__(name)

        logger = self
        logger.setLevel(logging.DEBUG)

        # initialize logger for standard out
        stout_formatter = logging.Formatter(
            fmt="[%(asctime)s][%(levelname)-3.3s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(stout_formatter)
        stdout_handler.setLevel(logging.WARN)
        logger.addHandler(stdout_handler)

        self.__logger = logger
        self.__stdout_handler = stdout_handler
        self.__logfile_handler = None

    def enable_filehandler(self, filename):

        if self.__logfile_handler:
            self.warning("filehandler is already enabled.")
            return

        # initialize logger for the log file
        logfile_formatter = logging.Formatter(
            fmt="[%(asctime)s][%(levelname)-3.3s][%(filename)s:%(lineno)d] %(funcName)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        log_filename = filename
        logfile_handler = RotatingFileHandler(log_filename, maxBytes=(1048576 * 5), backupCount=2)
        logfile_handler.setFormatter(logfile_formatter)
        logfile_handler.setLevel(LOGGER_LOG_LEVEL)
        self.__logger.addHandler(logfile_handler)

        self.__logfile_handler = logfile_handler

    def set_verbose(self):
        self.__stdout_handler.setLevel(logging.INFO)

    def notice(self, message):
        """Notice a message to a user.
        Args:
            message: the message to notice to the user.
        """
        self.__logger.log(100, message)
