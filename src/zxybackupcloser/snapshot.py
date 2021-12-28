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
import re

from zxybackupcloser.command import Command

######################
#    ZFS Commands    #
######################
CMD_ZFS_LIST_SCRIPT: Final[str] = "zfs list -H"
# Display the names of the snapshots on the specified pool.
CMD_ZFS_LIST_SNAPSHOT: Final[str] = CMD_ZFS_LIST_SCRIPT + " -o name -t snapshot {pool}"

######################
#    Script Code     #
######################

LOGGER = None


class Snapshot:
    """Snapshot class on ZFS filesystem.
    Snapshot only accept the existence ZFS pools.
    """

    @classmethod
    def initialize(cls, logger, dryrun, snapshoter):
        global LOGGER
        LOGGER = logger
        cls.__dryrun = dryrun
        cls.__snapshoter = snapshoter

    def __init__(self, pool):
        """Construct a snapshot instance with the ZFS pool name specified.
        Args:
            pool: The name of a ZFS pool.
        """
        LOGGER.debug(f"STR: {pool}")

        self.__pool = pool
        self.__latest_raw = ""
        self.__snapshots = self.__get_list(self.__pool)

        LOGGER.debug(f"END")

    def take(self):
        """Take a snapshot now.
        """
        LOGGER.debug(f"STR")

        dry_option = "-n" if self.__dryrun else ""

        # self.__snapshoter commandline as:
        # ZFS_AUTO_SNAPSHOT_SHORTEST: Final[str] = "zfs-auto-snapshot {dryrun} -qr --label=hourly {pool}"

        snapshot_commandline = self.__snapshoter.format(dryrun=dry_option, pool=self.__pool)
        snapshot_command = Command(snapshot_commandline)
        output = snapshot_command.execute(always=True)

        if self.__dryrun:
            # get the output if dryrun auto-snapshot
            # the output: zfs snapshot -o com.sun:auto-snapshot-desc='-'  'pool1@zfs-auto-snap_hourly-2021-12-11-0557'
            snapshot_name = output.split("'")[-2]
            self.__latest_raw = snapshot_name

        # dispose the old snapshots
        self.__snapshots = self.__get_list(self.__pool)

        LOGGER.debug(f"END")

    def __get_list(self, pool) -> list[str]:
        """Get all of the snapshots on the pool sorted by time in reverse order.
        Args:
            pool: The name of a ZFS pool.
        Returns:
            list[str]: The list of the snapshot names on the pool sorted by time in reverse order.
        """

        # get the list of snapshots on the pool if the pool exists, otherwise the empty list
        list_snap_cmd = Command(CMD_ZFS_LIST_SNAPSHOT.format(pool=pool))
        output = list_snap_cmd.execute(always=True)

        snapshots = output.strip().splitlines()
        snapshots.sort(key=lambda s: re.search(r"\d{4}-\d{2}-\d{2}-\d{4}", s).group(), reverse=True)

        # add the latest snapshot into the list on memory if under dry-run
        if self.__dryrun and len(self.__latest_raw) > 0:
            snapshots.insert(0, self.__latest_raw)
            LOGGER.info(f"Add the {self.__latest_raw} snapshot into the list on memory.")

        return snapshots

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

    def constain_snapshot(self, name):
        """Confirm this instance contains a name of the snapshot.
        Args:
            name: A name of snapshot.
        Returns:
            bool: True if this instance contains the snapshot.
        """
        result = name in self.__snapshots
        return result

    def get_list(self) -> list[str]:
        """Get all of the snapshots on the pool sorted by time in reverse order.
        Returns:
            list[str]: The list of the snapshot names on the pool sorted by time in reverse order.
        """
        return self.__snapshots

    def get_earliest(self):
        earliest = self.__snapshots[len(self.__snapshots) - 1]
        return earliest

    def get_latest(self):
        latest = self.__snapshots[0]
        return latest
