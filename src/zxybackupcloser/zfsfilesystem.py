#!/usr/bin/env python3

# Copyright (c) 2021 Patineboot. All rights reserved.
# ZxyBackupCloser is licensed under BSD 2-Clause License.

from typing import ClassVar, Final
import io
import sys
import getpass

from zxybackupcloser.command import Command


######################
#    ZFS Commands    #
######################
CMD_ZFS_LIST_SCRIPT: Final[str] = "zfs list -H"
# Display the names of the ZFS pool and dataset on the system.
CMD_ZFS_LIST_FILESYSTEM: Final[str] = CMD_ZFS_LIST_SCRIPT + " -o name -t filesystem"
# Display the names of the ZFS pool and dataset on the system.
CMD_ZFS_LIST_MOUNTED: Final[str] = CMD_ZFS_LIST_SCRIPT + " -r -o name,encryptionroot,mounted -t filesystem {pool}"

# Mount the specified dataset on the ZFS filesystem.
CMD_ZFS_MOUNT: Final[str] = "zfs mount -l {dataset}"
# Unmount the specified datasets on the ZFS filesystem.
CMD_ZFS_UNMOUNT: Final[str] = "zfs unmount -u {dataset}"

# Set disable auto-snapshot which you take with zfs-auto-snapshot.
CMD_DISABLE_AUTO_SNAPSHOT: Final[str] = "zfs set com.sun:auto-snapshot=false {pool}"

LOGGER = None

PASSPHRASE_PROMPT: Final[str] = """
Get the difference of the backups from previous to present.
Mount the encryption dataset[s] with your passphrase for the diff.
See the '-d', '--diff' option.
Enter Passphrase for the ZFS dataset[s]:"""


class ZfsFilesystem:

    __instance: ClassVar['ZfsFilesystem'] = None

    @classmethod
    def initialize(cls, logger):
        global LOGGER
        LOGGER = logger

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

        self.__passphrase = ""

        list_command = Command(CMD_ZFS_LIST_FILESYSTEM)
        output = list_command.execute(always=True)
        self.__pools = output.strip().splitlines()

        LOGGER.debug(f"END")

    def exist(self, pool):
        """Confirm a pool exists.
        Args:
            pool: The name of a ZFS pool.
        Return:
            bool: True if a pool exists.
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
        disable_snapshot_commandline = CMD_DISABLE_AUTO_SNAPSHOT.format(pool=pool)
        disable_snapshot_command = Command(disable_snapshot_commandline)
        disable_snapshot_command.execute()

        LOGGER.debug(f"END")

    def prompt_passphrase(self):
        """Ask for your passphrase.
        """
        LOGGER.debug(f"STR")

        if sys.stdin.isatty():
            self.__passphrase = getpass.getpass(prompt=PASSPHRASE_PROMPT)
        else:
            self.__passphrase = sys.stdin.readline().rstrip()

        LOGGER.debug(f"END")

    def mount_pool(self, pool):
        """Mount a pool with recursive datasets.
        Args:
            pool: The name of a ZFS pool.
        Return:
            mountpoints: The snapshot of the mountpoints at the starting.
        """
        LOGGER.debug(f"STR: {pool}")

        command = Command(CMD_ZFS_LIST_MOUNTED.format(pool=pool))
        output = command.execute(always=True)
        mountpoints = [line.split("\t") for line in output.strip().splitlines()]

        for mountpoint in mountpoints:
            if mountpoint[2] == "yes":
                continue

            ppstream = None
            # send the passphrase to standard input if encryptionroot.
            if mountpoint[1] != "-":
                keybin = self.__passphrase.encode()
                ppstream = io.BytesIO(keybin)

            dataset = mountpoint[0]
            command = Command(CMD_ZFS_MOUNT.format(dataset=dataset))
            command.execute(stdin_input=ppstream)

        LOGGER.debug(f"END: {mountpoints}")
        return mountpoints

    def unmount_pool(self, pool):
        """Unmount a pool with recursive datasets.
        Args:
            pool: The name of a ZFS pool.
        Return:
            mountpoints: The snapshot of the mountpoints at the starting.
        """
        LOGGER.debug(f"STR: {pool}")

        command = Command(CMD_ZFS_LIST_MOUNTED.format(pool=pool))
        output = command.execute(always=True)
        mountpoints = [line.split("\t") for line in output.strip().splitlines()]
        mountpoints.reverse()

        for mountpoint in mountpoints:
            if mountpoint[2] == "yes":
                command = Command(CMD_ZFS_UNMOUNT.format(dataset=mountpoint[0]))
                command.execute()

        LOGGER.debug(f"END: {mountpoints}")
        return mountpoints

    def unmount_dataset(self, mountpoints):
        """Unmount datasets specified on mountpoints.
        Args:
            mountpoints: The snapshot of the mountpoints at the starting.
        """
        LOGGER.debug(f"STR: {mountpoints}")

        for mountpoint in mountpoints:
            if mountpoint[2] == "no":
                command = Command(CMD_ZFS_UNMOUNT.format(dataset=mountpoint[0]))
                command.execute()

        LOGGER.debug(f"END")

    def has_encryptionroot(self, pools):
        """Confirm a pool has a dataset set on encryptionroot.
        Args:
            pools: The name of some ZFS pools to confirm.
        Return:
            bool: True if a pool has a dataset set on encryptionroot.
        """
        LOGGER.debug(f"STR: {pools}")

        command = Command(CMD_ZFS_LIST_MOUNTED.format(pool=" ".join(pools)))
        output = command.execute(always=True)
        mountpoints = [line.split("\t") for line in output.strip().splitlines()]

        encryptionroots = [mountpoint[1] for mountpoint in mountpoints if mountpoint[1] != "-"]
        result = len(encryptionroots) > 0

        LOGGER.debug(f"END: {result}")
        return result
