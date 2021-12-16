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

from typing import ClassVar, Final

import os
import subprocess
import re
import tempfile
import logging

from zxybackupcloser.commandoption import CommandOption
from zxybackupcloser.printlogger import PrintLogger


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
# Display the names of the ZFS pool and dataset on the system.
CMD_ZFS_LIST: Final[str] = "zfs list -H -o name"
# Create the dataset on a backup pool with an original pool name.
CMD_CREATE_DATASET: Final[str] = "zfs create -p {}"
# Display the names of the snapshots on the specified pool.
CMD_ZFS_LIST_SNAPSHOT: Final[str] = CMD_ZFS_LIST + " -t snapshot {}"
# Send the snapshots between start and end, receive and store the snapshots.
CMD_SNAPSHOT_SEND: Final[str] = "zfs send -Rw {} {} {} | tee >(zstreamdump > {}) | pv | zfs recv -F -d {}"
# zfs -I option
SEND_I_OPTION: Final[str] = "-I"
# Send the snapshots between start and end.
CMD_ZSTREAMDUMP: Final[str] = "zfs send -Rw -I {} {} | zstreamdump"
# Set disable auto-snapshot which you take with zfs-auto-snapshot.
CMD_DISABLE_AUTO_SNAPSHOT: Final[str] = "zfs set com.sun:auto-snapshot=false {pool}"
# Dry run the snapshots between start and end.
CMD_SEND_DRYRUN: Final[str] = "zfs send -vn {} {} {}"


######################
#    Script Code     #
######################

# Parse the command options
logging.setLoggerClass(PrintLogger)
LOGGER: Final[PrintLogger] = logging.getLogger(__name__)

comand_options = CommandOption(LOGGER)


def execute(command, input=None, check=True, dry=False):
    """Run a command.
    Args:
        command: A shell command with some options if existed.
        input: The standard input of the first commands.
        check: If True, raise exception if the one or more commands return a error code.
        dry: If true, print the command and no others occur.
    Returns:
        str: The stdout of the command.
    """

    LOGGER.debug(f"STR: {command}, {input}, {check}")

    LOGGER.info(f"CMD: {command}")
    if comand_options.get_dryrun() and dry:
        return ""

    process = subprocess.run(
        command, shell=True, executable="/bin/bash",
        text=True, input=input, stdout=subprocess.PIPE)
    if process.returncode != 0:
        LOGGER.error(f"command: {process.args}")
        LOGGER.error(f"error code: {process.returncode}")
        LOGGER.error(f"stdout: {process.stdout}")
        LOGGER.error(f"stderr: {process.stderr}")
        if check:
            process.check_returncode()

    LOGGER.debug(f"CMD returncode: {process.returncode}")
    LOGGER.debug(f"CMD stdout: {process.stdout}")
    LOGGER.debug(f"CMD stderr: {process.stderr}")

    LOGGER.debug(f"END")
    return process.stdout


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

        LOGGER.debug(f"END")

    def prepare(self):
        """Prepare to back up.
        Returns:
            bool: False if up-to-date backup.
        """
        LOGGER.debug(f"STR")

        # Create the datasets on the backup pool.
        create_dataset_command = CMD_CREATE_DATASET.format(self.__destination)
        execute(create_dataset_command, dry=True)
        pool_snap = Snapshot(self.__pool)
        dest_snap = Snapshot(self.__destination)

        self.__earliest = pool_snap.earliest(dest_snap)
        self.__latest = pool_snap.get_list()[0]

        result = True
        if self.__earliest == self.__latest:
            LOGGER.notice(f"The backup of {self.__pool} up-to-date.")
            LOGGER.notice(f"The latest snapshot, {self.__latest}, exists on the backup.")
            result = False
        self.__pool_snapshot = pool_snap

        LOGGER.debug(f"END: {result}")
        return result

    def __send(self, earliest, latest, destination) -> str:
        """Send the ZFS pool and receive it on the destination.
        Args:
            earliest: The name of the earliest of the snapshots on the pool to send first.
            latest: The name of the latest of the snapshots on the pool to send last.
        Returns:
            str: A portable MAC
        """
        i_option = SEND_I_OPTION

        # specify the only one snapshot
        if latest == "":
            i_option = ""

        # Print total estimated size
        send_dryrun_command = CMD_SEND_DRYRUN.format(
            i_option, earliest, latest)
        output = execute(send_dryrun_command, dry=True)
        estimated = output.strip().splitlines()
        LOGGER.notice(estimated[len(estimated) - 1])

        # Send total estimated size
        with tempfile.NamedTemporaryFile(mode="r") as file:
            snapshot_send_command = CMD_SNAPSHOT_SEND.format(
                i_option, earliest, latest, file.name, self.__destination)
            execute(snapshot_send_command, dry=True)
            summary = file.read()

            return summary

    def backup(self):
        """Back up the ZFS pool.
        """
        LOGGER.debug(f"STR")

        # back up the earliest snapshot on the pool
        # if the destination dataset and the pool all have different snapshots.
        if self.__earliest is None:
            snaps = self.__pool_snapshot.get_list()
            size = len(snaps)
            earliest = snaps[size - 1]

            self.__send(earliest, "", self.__destination)
            self.__earliest = earliest

        # get the name of the latest snapshot on the pool.
        # send the snapshots from the earliest to the latest on the pool.
        self.__summary = self.__send(self.__earliest, self.__latest, self.__destination)

        LOGGER.debug(f"END")

    def verify(self):
        """Verify the backup.
        Returns:
            bool: True if verified, otherwise failed.
        """
        LOGGER.debug(f"STR")

        earliest_snapshot = self.__earliest.replace(self.__pool, self.__destination, 1)
        latest_snapshot = self.__latest.replace(self.__pool, self.__destination, 1)

        # get a summary briefing the backup
        zstreamdump_command = CMD_ZSTREAMDUMP.format(
            earliest_snapshot, latest_snapshot, self.__destination)
        backup_summary = execute(zstreamdump_command, dry=True)

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
        LOGGER.debug(f"STR: {summary}")

        line_pattern = r"\s*portable_mac = (0x[0-9a-f]{2} )+"
        mac = summary.splitlines()
        mac = [s for s in mac if re.match(line_pattern, s)]

        LOGGER.debug(f"END: {mac}")
        return mac


class Snapshot:
    """Snapshot class on ZFS filesystem.
    Snapshot only accept the existence ZFS pools.
    """

    def __init__(self, pool):
        """Construct a snapshot instance with the ZFS pool name specified.
        Args:
            pool: The name of a ZFS pool.
        """
        LOGGER.debug(f"STR: {pool}")

        self.__pool = pool
        self.__is_dry = comand_options.get_dryrun()
        self.__latest = ""
        self.__snapshots = []

        LOGGER.debug(f"END")

    def take(self):
        """Take a snapshot now.
        """
        LOGGER.debug(f"STR")

        dry_option = "n" if self.__is_dry else ""

        take_snapshot_cmd = ZFS_AUTO_SNAPSHOT_SHORTEST.format(dryrun=dry_option, pool=self.__pool)
        output = execute(take_snapshot_cmd, dry=False)
        # output like [zfs snapshot -o com.sun:auto-snapshot-desc='-'  'pool1@zfs-auto-snap_hourly-2021-12-11-0557']

        snapshot_name = output.split("'")[-1]
        self.__latest = snapshot_name

        # dispose the old snapshots
        self.__snapshots = []

        LOGGER.debug(f"END")

    def __get_list(self, pool) -> list[str]:
        """Get all of the snapshots on the pool sorted by time in reverse order.
        Args:
            pool: The name of a ZFS pool.
        Returns:
            list[str]: The list of the snapshot names on the pool sorted by time in reverse order.
        """
        LOGGER.debug(f"STR: {pool}")

        zfilesystem = ZfsFilesystem.get_instance()

        # get the list of snapshots on the pool if the pool exists, otherwise the empty list
        list_snapshot_cmd = CMD_ZFS_LIST_SNAPSHOT.format(pool)
        output = execute(list_snapshot_cmd) if zfilesystem.exist(pool) else ""

        snapshots = output.strip().splitlines()
        snapshots.sort(key=lambda s: re.search(r"\d{4}-\d{2}-\d{2}-\d{4}", s).group(), reverse=True)

        # add the latest snapshot into the list on memory if under dry-run
        if pool in comand_options.get_pools() and \
                self.__is_dry and \
                self.__latest:
            snapshots.insert(0, self.__latest)
            LOGGER.info(f"Add the {self.__latest} snapshot into the list on memory.")

        LOGGER.debug(f"END: {snapshots}")
        return snapshots

    def get_list(self) -> list[str]:
        """Get all of the snapshots on the pool sorted by time in reverse order.
        Returns:
            list[str]: The list of the snapshot names on the pool sorted by time in reverse order.
        """
        LOGGER.debug(f"STR")

        if not self.__snapshots:
            snapshots = self.__get_list(self.__pool)
            self.__snapshots = snapshots
        LOGGER.debug(f"END: {self.__snapshots}")

        return self.__snapshots

    def earliest(self, snapshot) -> str:
        """Find the earliest snapshot which both this and the specified instance contain.
        Args:
            snapshot: A snapshot instance.
        Returns:
            str: The earliest snapshot
        """
        LOGGER.debug(f"STR: {snapshot}")

        # Find the start snapshot.
        earliest = None

        for bsnap in snapshot.get_list():
            for osnap in self.get_list():
                blabel = bsnap.split("@")[1]
                olabel = osnap.split("@")[1]
                if (blabel == olabel):
                    earliest = osnap
                    break
            else:
                continue
            break

        LOGGER.debug(f"END: {earliest}")
        return earliest


class ZfsFilesystem:

    __instance: ClassVar['ZfsFilesystem'] = None

    @classmethod
    def get_instance(cls) -> 'ZfsFilesystem':
        """ Get the instance of the ZfsFilesystem class.
        Return:
            ZfsFilesystem: The singleton instance.
        """
        LOGGER.debug(f"STR")

        if not cls.__instance:
            instance = ZfsFilesystem()
            cls.__instance = instance

        LOGGER.debug(f"END")
        return cls.__instance

    def __init__(self):
        """Construct a ZfsList instance.
        """
        LOGGER.debug(f"STR")

        zfs_list_cmd = CMD_ZFS_LIST
        output = execute(zfs_list_cmd)
        self.__pools = output.strip().splitlines()

        LOGGER.debug(f"END")

    def exist(self, pool):
        """Return True if the pool exists.
        Args:
            pool: The name of a ZFS pool.
        """
        LOGGER.debug(f"STR: {pool}")

        result = pool in self.__pools

        LOGGER.debug(f"END: {result}")
        return result

    def disable_auto_snapshot(self, pool):
        """Disable auto-snapshot.
        Args:
            pool: The name of a ZFS pool.
        """
        LOGGER.debug(f"STR: {pool}")

        # Disable auto-snapshot which the "zfs set com.sun:auto-snapshot=false" command
        disable_snapshot_command = CMD_DISABLE_AUTO_SNAPSHOT.format(pool=pool)
        execute(disable_snapshot_command, dry=True)

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

        if not is_root and not comand_options.get_user():
            LOGGER.error("Run this script with **sudo**.")
            return

        zfilesystem = ZfsFilesystem.get_instance()

        # exit if the pools or the backup pool do not exist.
        pools = comand_options.get_pools()
        backup_pool = comand_options.get_backup()

        zfs_pools = list(pools)
        zfs_pools.append(backup_pool)
        for pool in zfs_pools:
            if not zfilesystem.exist(pool):
                LOGGER.error(f"{pool} is not exist.")
                return

        # disable auto-snapshot
        zfilesystem.disable_auto_snapshot(backup_pool)

        # start the backup process
        for pool in pools:
            snapshot = Snapshot(pool)
            snapshot.take()

            process = Backup(pool, backup_pool)
            if not process.prepare():
                continue

            process.backup()
            process.verify()

    except BaseException:
        print("An exception occurs")
        raise
    finally:
        LOGGER.debug("LOG END")


if __name__ == "__main__":
    launch()


def get_checksums(stream_dump):
    """(To be used in the future) Get all the checksums from stream_dump.
    Args:
        stream_dump: an output of the zstreamdump command.
    """

    LOGGER.debug(f"STR: {stream_dump}")

    line_pattern = r"END checksum = [0-9a-f]+/[0-9a-f]+/[0-9a-f]+/[0-9a-f]+"
    checksums = stream_dump.splitlines()
    checksums = [s for s in checksums if re.match(line_pattern, s)]

    LOGGER.debug(f"END")
    return checksums


def verify_backups_with_checksum(snapshots, first_snapshot, summary, backup_dataset):
    """(To be used in the future)Verify the specified backup.
    Args:
        snapshots: All the snapshots on the original pool.
        first_snapshot: The first snapshot.
        summary: A summary of all the snapshot.
        backup_dataset: A backup dataset.
    """

    LOGGER.debug(f"STR: {snapshots}, {first_snapshot}, {summary}, {backup_dataset}")

    latest_snapshot_name = snapshots[0].split("@")[1]
    latest_backup_snapshot = f"{backup_dataset}@{latest_snapshot_name}"

    first_snapshot_name = first_snapshot.split("@")[1]
    first_backup_snapshot = f"{backup_dataset}@{first_snapshot_name}"

    backup_summary: str
    # Send all the snapshots from the first to the latest on the snapshots.
    zstreamdump_command = CMD_ZSTREAMDUMP.format(
        first_backup_snapshot, latest_backup_snapshot, backup_dataset)
    backup_summary = execute(zstreamdump_command, dry=True)

    checksum = get_checksums(summary)
    backup_checksum = get_checksums(backup_summary)

    LOGGER.info(f"checksum: {checksum}")
    LOGGER.info(f"backup_checksum: {backup_checksum}")

    succeeded = checksum == backup_checksum

    LOGGER.debug(f"END")
    return succeeded
