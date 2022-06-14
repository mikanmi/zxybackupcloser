#!/bin/bash -eu

# the original pools: home.pool, storage.pool
# the destination pool: backup.pool
# back up the original pools and verify the storage dataset on storage.pool.

# Wait for a user to input passphrase.
read -sp "Enter Passphrase for ZFS dataset: " passphrase
echo

# Import backup.pool on attached external storage.
zpool import backup.pool

# back up the original pools
echo -n $passphrase | zxybackupcloser -d -b backup.pool home.pool storage.pool

# verifiy storage.pool.
echo $passphrase | zfs mount -l backup.pool/storage.pool/storage
rsync -n -carv --delete /storage.pool/storage/ /backup.pool/storage.pool/storage

zpool export backup.pool
