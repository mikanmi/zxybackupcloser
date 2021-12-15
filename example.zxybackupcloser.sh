#!/bin/bash -eu

#
# the original pools: root-pool, storage-pool
# the destination pool: backup-pool
# back up the pools and verify the archive dataset only.

# wait for a user to input passphrase
read -sp "Enter Passphrase for ZFS dataset: " passphrase
echo

# import backup-pool on attached external storage.
zpool import backup-pool

# back up the original pools
zxybackupcloser -b backup-pool root-pool storage-pool

# verifiy storage-pool only.
echo $passphrase | zfs mount -l backup-pool/storage-pool/archive
rsync -n -carv --delete /storage-pool/archive/ /backup-pool/storage-pool/archive

zpool export backup-pool
