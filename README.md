# ZxyBackupCloser

ZxyBackupCloser is a backup application to back up some ZFS pools to another ZFS pool or dataset.

Patineboot is backing up all the ZFS pools on internal SSDs to an external SSD with ZxyBackupCloser every time.

## Feature

You can back up your ZFS pools with one command, only ZxyBackupCloser.

- ZxyBackupCloser backs up some ZFS pools involving all of the snapshots.
- ZxyBackupCloser supports incremental backup from the previous backup.
- ZxyBackupCloser verifies the backup with the portable mac from the backup and the original ZFS pool.

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

Reference:

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

Note: remove the com.sun:auto-snapshot property of the original pools, or you will take snapshots to disturb.

Remove the com.sun:auto-snapshot property:

```bash
sudo zfs inherit com.sun:auto-snapshot <pool name>'
```

### Optional Usage

See more detail of usage, run the `zxybackupcloser` command with the `-h` option.

```bash
$ zxybackupcloser -h

usage: zxybackupcloser [-h] -b BACKUP [-v] [-n] [-u] pool [pool ...]

ZxyBackupCloser is a backup application to back up some ZFS pools to another ZFS pool or dataset.

positional arguments:
  pool                  specify one or more names of the original ZFS pools.

optional arguments:
  -h, --help            show this help message and exit
  -b BACKUP, --backup BACKUP
                        specify the name of the pool or dataset to store the original pools.
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

ZxyBackupCloser is running on the following but not limited.

OS: Ubuntu Server 21.04

- Python 3.9.5
- ZFS on Linux 2.0.2
- GNU bash, version 5.1.4
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
