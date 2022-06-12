# ZxyBackupCloser

ZxyBackupCloser is an easy backup application to store your ZFS pools containing a lot of snapshots to another ZFS pool or dataset.

Patineboot is backing up all Patineboot's ZFS pools on internal SSDs to an external SSD with **ZxyBackupCloser** every time.

## Feature

You back up your ZFS pools with the one command, only ZxyBackupCloser.

- ZxyBackupCloser keeps all of the snapshots of your ZFS pools in the backup ZFS pools.
- ZxyBackupCloser supports the incremental backup from the previous backup.
- ZxyBackupCloser verifies the original and the backup ZFS pools with the portable mac.
- ZxyBackupCloser gets the difference between the previous and the present backup ZFS pools.

## Install ZxyBackupCloser (Recommend)

1. Install ZxyBackupCloser from PyPI.

   Install `zxybackupcloser` with the `pip3` command.

   ```bash
   pip3 install zxybackupcloser
   ```

### Dependency

1. 'Pipe Viewer' and 'zfs-auto-snapshot'

   Install 'Pipe Viewer' and 'zfs-auto-snapshot' with `apt`.

   ```bash
   apt install pv zfs-auto-snapshot
   ```

Get more information:

- [Pipe Viewer](https://www.ivarch.com/programs/pv.shtml)
- [zfs-auto-snapshot](https://github.com/zfsonlinux/zfs-auto-snapshot)

## Usage

### Basic Usage

Back up your ZFS pools with `zxybackupcloser`:

```bash
zxybackupcloser -b <backup pool> <original pools>
```

- _\<original pools>_: specify the one or more names of the original ZFS pools.
- _\<backup pool\>_: specify the name of the destination pool or dataset to store the original pools.

e.g., we back up two of the original pools named _root-pool_ and _storage-pool_ to the _backup-pool_ pool.

```bash
sudo zxybackupcloser -b backup-pool root-pool storage-pool
```

_Note_: Reboot the machine if a pool on the ZFS filesystem does not unmount. ZxyBackupCloser unmounts the backup pool on its own backup process.

_Note_: Remove the com.sun:auto-snapshot property of the original pools, or you will take snapshots on the backup pool to disturb the backup pool.

Remove the com.sun:auto-snapshot property:

```bash
sudo zfs inherit com.sun:auto-snapshot <pool name>
```

### Optional Usage

See more detail of usage, run the `zxybackupcloser` command with the `-h` option.

```bash
$ zxybackupcloser -h

usage: zxybackupcloser [-h] -b BACKUP [-d] [-v] [-n] [-u] pool [pool ...]

ZxyBackupCloser is a backup application to back up some ZFS pools to another ZFS pool or dataset.

positional arguments:
  pool                  specify one or more names of the original ZFS pools.

optional arguments:
  -h, --help            show this help message and exit
  -b BACKUP, --backup BACKUP
                        specify the name of the pool or dataset to store the original pools.
  -d, --diff            get the difference of the backups from previous to present.
  -v, --verbose         run with verbose mode.
  -n, --dry-run         run with no changes made.
  -u, --user            run on your normal user account.
```

### Advanced Configure

I prepared the macros for advanced configuration on the _backupcloser.py_ script file.
Change the macros for taking the snapshots and logging while backing up.

Notice: you can find the place of the _backupcloser.py_ file with `pip3 show zxybackupcloser`.

## Install and run ZxyBackupCloser from GitHub

1. Get ZxyBackupCloser from GitHub.com

   Get ZxyBackupCloser with `git clone`:

   ```bash
   git clone https://github.com/patineboot/zxybackupcloser.git
   ```

2. Run the `backupcloser.py` script

   Move the current directory to the script directory by `cd zxybackupcloser/src/zxybackupcloser` and run the `backupcloser.py` script:

   ```bash
   cd ./zxybackupcloser/src/zxybackupcloser
   sudo ./backupcloser.py -h
   ```

## Environment

Patineboot is running ZxyBackupCloser with the following software environment.
Patineboot thinks ZxyBackupCloser can run with other software or versions.

OS: Ubuntu Server 21.04

- Python 3.9.5
- ZFS on Linux 2.0.2
- pv 1.6.6
- zfs-auto-snapshot 1.2.4

## Deploy ZxyBackupCloser for development

Run ZxyBackupCloser while developing:

```bash
sudo PYTHONPATH=../ ./backupcloser.py -b <backup pool> <original pools>
```

Deploy ZxyBackupCloser on PyPI:

```bash
python3 -m build
python3 -m twine upload dist/*
```

twine asks:

```bash
User: patineboot
Pass: <your passphrase>
```

Reference: [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
