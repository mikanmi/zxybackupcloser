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
import re
import enum
import logging


from zxybackupcloser.command import Command
from zxybackupcloser.commandoption import CommandOption
from zxybackupcloser.printlogger import PrintLogger
from zxybackupcloser.zfsfilesystem import ZfsFilesystem
from zxybackupcloser.snapshot import Snapshot

######################
# Advanced Configure #
######################
# zfs-auto-snapshot of the cron shell script for the shortest interval one.
ZFS_AUTO_SNAPSHOT_SHORTEST: Final[str] = "zfs-auto-snapshot {dryrun} -qr --label=hourly {pool}"

LOGGER_LOG_ROOT_PATH: Final[str] = "/var/log/"
LOGGER_LOG_USER_PATH: Final[str] = os.environ.get("HOME") + "/"
LOGGER_LOG_FILENAME: Final[str] = "zxybackupcloser.log"

######################
#    ZFS Commands    #
######################
CMD_ZFS_LIST_SCRIPT: Final[str] = "zfs list -H"
# Recursively display the names of any childlen of the ZFS pool and dataset on the system.
CMD_ZFS_LIST_RECURSIVE: Final[str] = CMD_ZFS_LIST_SCRIPT + " -r -o name -t filesystem {pool}"

# Create the dataset on a backup pool with an original pool name.
CMD_ZFS_CREATE: Final[str] = "zfs create -p {pool}"

# The zfs send command
CMD_ZFS_SEND: Final[str] = "zfs send -Rw {options} {earliest} {latest}"
# Send the intermediate snapshots of the zfs send option.
SEND_OPTION_INTERMIDIATE: Final[str] = "-I"
# Dry run and verbose for estimated size of the zfs send option.
SEND_OPTION_ESTIMATEDSIZE: Final[str] = "-vn"

# The zfs receive command
CMD_ZFS_RECV: Final[str] = "zfs recv -F -d -x mountpoint {dataset}"

# Display the difference between a snapshot and the later snapshot or present.
CMD_ZFS_DIFF: Final[str] = "zfs diff {snapshot} {filesystem}"


# The zstreamdump command
CMD_ZSTREAMDUMP: Final[str] = "zstreamdump"


########################
# Command Applications #
########################
# The Pipe View command
CMD_PV: Final[str] = "pv"

######################
#    Script Code     #
######################
# Parse the command options
logging.setLoggerClass(PrintLogger)
LOGGER: Final[PrintLogger] = logging.getLogger(__name__)

comand_options = CommandOption(LOGGER)


class BackupType(enum.Enum):
    KEEP = 1
    NORMAL = 2
    ALL = 3


class BackupParam:

    def __init__(self, backup_type, earliest, latest):
        self.backup_type = backup_type
        self.earliest = earliest
        self.latest = latest


class Backup:

    def __init__(self, pool, backup_pool):
        """Construct Backup instance,
        Args:
            pool: The name of a ZFS pool to back up.
            backup_pool: The name of a ZFS pool to which you back up the pool.
        """
        LOGGER.debug(f"STR: {pool}, {backup_pool}")

        self.__pool = pool
        # Make a dataset name to which you back up the pool.
        self.__destination = f"{backup_pool}/{pool}"

        self.__earliest = ""
        self.__latest = ""
        self.__backup_type = BackupType.ALL

        LOGGER.debug(f"END")

    def prepare(self):
        """Prepare to back up.
        Returns:
            bool: False if up-to-date backup.
        """
        LOGGER.debug(f"STR")

        # Create the datasets on the backup pool.
        create_commandline = CMD_ZFS_CREATE.format(pool=self.__destination)
        create_command = Command(create_commandline)
        create_command.execute()

        pool_snap = Snapshot(self.__pool)
        pool_snap.take()
        dest_snap = Snapshot(self.__destination)

        # common earliest of the pool and the backup pool.
        earliest = pool_snap.earliest(dest_snap)
        latest = pool_snap.get_latest()

        # Decide BackupType
        backup_type = BackupType.NORMAL

        # The backup pool is up to date.
        if earliest == latest:
            backup_type = BackupType.KEEP

        # Back up all snapshots on the pool,
        # if the destination dataset and the pool do not have even one of the same snapshots.
        elif earliest is None:
            earliest = pool_snap.get_earliest()
            backup_type = BackupType.ALL

        self.__backup_type = backup_type
        self.__earliest = earliest
        self.__latest = latest

        earliest_label = earliest.split("@")[1]
        latest_label = latest.split("@")[1]

        param = BackupParam(backup_type, earliest_label, latest_label)

        LOGGER.debug(f"END: {param}")
        return param

    def __send(self, earliest, latest, destination) -> str:
        """Send the ZFS pool and receive it on the destination.
        Args:
            earliest: The name of the earliest of the snapshots on the pool to send first.
            latest: The name of the latest of the snapshots on the pool to send last.
                    Specify "" if sending one snapshot only.
            destination: The name of the pool or dataset to store the snapshots between earlist and latest
        Returns:
            str: A portable MAC
        """

        i_option = SEND_OPTION_INTERMIDIATE if latest != "" else ""
        size_options = f"{SEND_OPTION_ESTIMATEDSIZE} {i_option}"

        # get total estimated size
        estimate_commandline = CMD_ZFS_SEND.format(
            options=size_options, earliest=earliest, latest=latest)
        estimate_command = Command(estimate_commandline)
        stdout_text = estimate_command.execute()

        # print total estimated size
        estimated = stdout_text.strip().splitlines()
        LOGGER.notice(estimated[len(estimated) - 1])

        # make the backup command
        # create send command
        backup_commandline = CMD_ZFS_SEND.format(
            options=i_option, earliest=earliest, latest=latest)
        backup_command = Command(backup_commandline)

        backup_command.add_subcommand(
            Command(CMD_ZSTREAMDUMP))

        pv_command = Command(CMD_PV)
        pv_command.handle_stderr(False)
        backup_command.add_subcommand(pv_command)

        recv_commandline = CMD_ZFS_RECV.format(dataset=destination)
        pv_command.add_subcommand(Command(recv_commandline))

        summary = backup_command.execute()

        return summary

    def backup(self):
        """Back up the ZFS pool.
        """
        LOGGER.debug(f"STR")

        # back up the earliest snapshot on the pool for backcup all
        if self.__backup_type == BackupType.ALL:
            self.__send(self.__earliest, "", self.__destination)

        # send the snapshots from the earliest to the latest on the pool,
        # if the pool has multiple snapshots.
        if self.__earliest != self.__latest:
            self.__summary = self.__send(self.__earliest, self.__latest, self.__destination)

        LOGGER.debug(f"END")

    def verify(self):
        """Verify the backup.
        Returns:
            bool: True if verified, otherwise failed.
        """
        LOGGER.debug(f"STR")

        succeeded = False

        # if one-shot backup only, skip the verifying for incremental backup.
        if self.__earliest == self.__latest:
            succeeded = True
            LOGGER.debug(f"END: {succeeded}")
            return succeeded

        i_option = SEND_OPTION_INTERMIDIATE
        earliest_snapshot = self.__earliest.replace(self.__pool, self.__destination, 1)
        latest_snapshot = self.__latest.replace(self.__pool, self.__destination, 1)

        # create send command
        backup_commandline = CMD_ZFS_SEND.format(
            options=i_option, earliest=earliest_snapshot, latest=latest_snapshot)
        backup_command = Command(backup_commandline)

        pv_command = Command(CMD_PV)
        pv_command.handle_stderr(False)
        backup_command.add_subcommand(pv_command)

        pv_command.add_subcommand(Command(CMD_ZSTREAMDUMP))
        backup_summary = backup_command.execute()

        # get MAC from the summaries
        mac = self.get_mac(self.__summary)
        backup_mac = self.get_mac(backup_summary)
        succeeded = mac == backup_mac

        LOGGER.debug(f"END: {succeeded}")
        return succeeded

    def get_mac(self, summary):
        """Get a portable MAC from the summary
        Args:
            summary: An output of the zstreamdump command.
        Returns:
            str: A portable MAC
        """
        # LOGGER.debug(f"STR: {summary}")
        LOGGER.debug(f"STR: input summary.")

        line_pattern = r"\s*portable_mac = (0x[0-9a-f]{2} )+"
        mac = summary.splitlines()
        mac = [s for s in mac if re.match(line_pattern, s)]

        LOGGER.debug(f"END: return MAC.")
        return mac

    def get_checksums(self, summary):
        """(To be used in the future) Get all the checksums from stream_dump.
        Args:
            stream_dump: an output of the zstreamdump command.
        """
        # LOGGER.debug(f"STR: {summary}")
        LOGGER.debug(f"STR: input summary.")

        line_pattern = r"END checksum = [0-9a-f]+/[0-9a-f]+/[0-9a-f]+/[0-9a-f]+"
        checksums = summary.splitlines()
        checksums = [s for s in checksums if re.match(line_pattern, s)]

        LOGGER.debug(f"END: return MAC.")
        return checksums


class Difference:
    """Diff class on ZFS filesystem.
    Get the difference between a snapshot and the later snapshot.
    """

    def __init__(self, pool, backup_pool):
        """Construct a Diff instance.
        Args:
            backup_pool: The name of the backup pool.
        """
        LOGGER.debug(f"STR: {pool}, {backup_pool}")

        # Make a dataset name to which you back up the pool.
        self.__destination = f"{backup_pool}/{pool}"

        LOGGER.debug(f"END")

    def diff(self, earliest_name, latest_name):
        """Get the difference between a snapshot and the later snapshot.
        Args:
            earliest_name: The name of a snapshot.
            latest_name: The name of the later snapshot then the snapshot.
        """
        LOGGER.debug(f"STR: {earliest_name}, {latest_name}")

        list_recursive_cmd = Command(CMD_ZFS_LIST_RECURSIVE.format(pool=self.__destination))
        lr_output = list_recursive_cmd.execute(always=True)
        datasets = lr_output.strip().splitlines()

        def stdio_handler(line):
            LOGGER.notice(line.rstrip(os.linesep))

        for dataset in datasets:
            earliest = f"{dataset}@{earliest_name}"

            snap = Snapshot(dataset)
            if not snap.constain_snapshot(earliest):
                earliest = snap.get_earliest()

            diff_cmd = Command(CMD_ZFS_DIFF.format(snapshot=earliest, filesystem=dataset))
            diff_cmd.execute(stdout_callback=stdio_handler)

        LOGGER.debug(f"END")


def backup_and_diff(pools, backup_pool):

    LOGGER.debug(f"STR: {pools}, {backup_pool}")

    zfilesystem = ZfsFilesystem.get_instance()

    # unmount the backup pool.
    # zfilesystem.unmount_pool(backup_pool)

    # disable auto-snapshot
    zfilesystem.disable_auto_snapshot(backup_pool)

    param_pool = {}

    # start the backup process
    for pool in pools:
        backup = Backup(pool, backup_pool)

        param = backup.prepare()
        param_pool[pool] = param

        # back up the next pool if the backup is up to date.
        if param.backup_type == BackupType.KEEP:
            LOGGER.notice(f"The backup of {pool} up-to-date.")
            LOGGER.notice(f"The latest snapshot, {param.latest}, exists on the backup.")
            continue

        backup.backup()
        backup.verify()

    if comand_options.get_diff():

        # set simple mode on standard output.
        if not comand_options.get_verbose():
            LOGGER.set_simple()

        # unmount the backup pool.
        mountpoints = zfilesystem.unmount_pool(backup_pool)

        # mount the all datasets on the backup pool
        zfilesystem.mount_pool(backup_pool)

        # load diff backup pool.
        for pool in pools:

            param: BackupParam = param_pool[pool]

            # the backup is up to date or first backup
            if param.backup_type == BackupType.KEEP:
                continue

            difference = Difference(pool, backup_pool)
            difference.diff(param.earliest, param.latest)

        # unmount the unmounted dataset at startup.
        zfilesystem.unmount_dataset(mountpoints)

    LOGGER.debug(f"END")


def launch():

    # check the root user
    is_root = os.geteuid() == 0 and os.getuid() == 0

    log_filename = (LOGGER_LOG_ROOT_PATH if is_root else LOGGER_LOG_USER_PATH) + LOGGER_LOG_FILENAME
    LOGGER.enable_filehandler(log_filename)

    LOGGER.debug("LOG START")
    try:
        # set verbose on the log mode.
        if comand_options.get_verbose():
            LOGGER.set_verbose()

        if not (is_root or comand_options.get_user()):
            LOGGER.error("Run this script with **sudo**.")
            return

        dryrun = comand_options.get_dryrun()
        Command.initialize(LOGGER, dryrun)
        ZfsFilesystem.initialize(LOGGER)
        Snapshot.initialize(LOGGER, dryrun, ZFS_AUTO_SNAPSHOT_SHORTEST)
        zfilesystem = ZfsFilesystem.get_instance()

        # exit if the pools or the backup pool do not exist.
        pools = comand_options.get_pools()
        backup_pool = comand_options.get_backup()

        zfs_pools = pools + [backup_pool, ]
        for pool in zfs_pools:

            if not zfilesystem.exist(pool):
                LOGGER.error(f"{pool} is not exist.")
                return

        # ask for your passphrase with the user prompt.
        if comand_options.get_diff() and zfilesystem.has_encryptionroot(pools):
            zfilesystem.prompt_passphrase()

        backup_and_diff(pools, backup_pool)

    except BaseException:
        print("An exception occurs")
        raise
    finally:
        LOGGER.debug("LOG END")


if __name__ == "__main__":
    launch()
