#!/usr/bin/env python3

# Copyright (c) 2021 Patineboot. All rights reserved.
# ZxyBackupCloser is licensed under BSD 2-Clause License.

import argparse

LOGGER = None


class CommandOption:

    def __init__(self, logger):
        global LOGGER
        LOGGER = logger

        # add command options to the argument parser.
        parser = argparse.ArgumentParser(
            description="The ZxyBackupCloser is to back up some ZFS pools to another ZFS pool or dataset."
        )
        parser.add_argument("-b", "--backup", required=True, help="specify the name of the pool or dataset to store the original pools.")
        parser.add_argument("-v", "--verbose", action="store_true", help="run with verbose mode.")
        parser.add_argument("-n", "--dry-run", dest='dry_run', action="store_true", help="run with no changes made.")
        parser.add_argument("-u", "--user", action="store_true", help="run on your normal user account.")
        parser.add_argument("pool", nargs="+", help="specify one or more names of the original ZFS pools.")

        self.__options = parser.parse_args()

    def get_backup(self):
        LOGGER.debug(f"STR")
        backup = self.__options.backup
        LOGGER.debug(f"END {backup}")
        return backup

    def get_verbose(self):
        LOGGER.debug(f"STR")
        verbose = self.__options.verbose
        LOGGER.debug(f"END {verbose}")
        return verbose

    def get_dryrun(self):
        LOGGER.debug(f"STR")
        dryrun = self.__options.dry_run
        LOGGER.debug(f"END {dryrun}")
        return dryrun

    def get_user(self):
        LOGGER.debug(f"STR")
        user = self.__options.user
        LOGGER.debug(f"END {user}")
        return user

    def get_pools(self):
        LOGGER.debug(f"STR")
        pools = self.__options.pool
        LOGGER.debug(f"END {pools}")
        return pools


if __name__ == "__main__":
    print("CommandOption is an Import Module.")
