#!/bin/bash -eu

# the original pools: root-pool, storage-pool
# the destination pool: backup-pool
# back up the pools and only verify the multimedia dataset.

# wait for a user to input passphrase
read -sp "Enter Passphrase for ZFS dataset: " passphrase
echo

# import backup-pool on attached external storage.
zpool import backup-pool

# back up the original pools
zxybackupcloser -v -b backup-pool root-pool storage-pool

# verifiy storage-pool only.
echo $passphrase | zfs mount -l backup-pool/storage-pool/multimedia
rsync -n -carv --delete /storage-pool/multimedia/ /backup-pool/storage-pool/multimedia

zpool export backup-pool
