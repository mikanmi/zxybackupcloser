#!/usr/bin/env python3

# Copyright (c) 2021,2022 Patineboot. All rights reserved.
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
        """Mount a pool and its datasets recursively.
        Args:
            pool: The name of the ZFS pool you mount.
        Return:
            The previous mount statuses: The list of pools or datasets, encryption roots, mount statuses at the calling this function.
            The result of `zfs list -r -o name,encryptionroot,mounted -t filesystem`.
        """
        LOGGER.debug(f"STR: {pool}")

        command = Command(CMD_ZFS_LIST_MOUNTED.format(pool=pool))
        output = command.execute(always=True)
        mount_statuses = [line.split("\t") for line in output.strip().splitlines()]

        for mount_status in mount_statuses:
            if mount_status[2] == "yes":
                continue

            ppstream = None
            # send the passphrase to the standard input of the mount command if encryptionroot is enabled.
            if mount_status[1] != "-":
                keybin = self.__passphrase.encode()
                ppstream = io.BytesIO(keybin)

            dataset = mount_status[0]
            command = Command(CMD_ZFS_MOUNT.format(dataset=dataset))
            command.execute(stdin_input=ppstream)

        LOGGER.debug(f"END: {mount_statuses}")
        return mount_statuses

    def unmount_pool(self, pool):
        """Unmount a pool and its datasets recursively.
        Args:
            pool: The name of the ZFS pool you unmount.
        Return:
            The previous mount statuses: The list of pools or datasets, encryption roots, mount statuses at the calling this function.
            The result of `zfs list -r -o name,encryptionroot,mounted -t filesystem`.
        """
        LOGGER.debug(f"STR: {pool}")

        command = Command(CMD_ZFS_LIST_MOUNTED.format(pool=pool))
        output = command.execute(always=True)
        mount_statues = [line.split("\t") for line in output.strip().splitlines()]
        mount_statues.reverse()

        for mount_status in mount_statues:
            if mount_status[2] == "yes":
                command = Command(CMD_ZFS_UNMOUNT.format(dataset=mount_status[0]))
                command.execute()

        LOGGER.debug(f"END: {mount_statues}")
        return mount_statues

    def unmount_dataset(self, mount_statuses):
        """Unmount datasets specified on mountpoints.
        Args:
            mount_statuses: The next mount statuses.
        """
        LOGGER.debug(f"STR: {mount_statuses}")

        for mount_status in mount_statuses:
            if mount_status[2] == "no":
                command = Command(CMD_ZFS_UNMOUNT.format(dataset=mount_status[0]))
                command.execute()

        LOGGER.debug(f"END")

    def has_encryptionroot(self, pools):
        """Confirm a pool in pools has a dataset with the encryptionroot property enabled.
        Args:
            pools: The list of the name of ZFS pools to confirm.
        Return:
            bool: True if a pool has a dataset with the encryptionroot property enabled.
        """
        LOGGER.debug(f"STR: {pools}")

        command = Command(CMD_ZFS_LIST_MOUNTED.format(pool=" ".join(pools)))
        output = command.execute(always=True)
        mount_statuses = [line.split("\t") for line in output.strip().splitlines()]

        encryptionroots = [mount_status[1] for mount_status in mount_statuses if mount_status[1] != "-"]
        result = len(encryptionroots) > 0

        LOGGER.debug(f"END: {result}")
        return result
