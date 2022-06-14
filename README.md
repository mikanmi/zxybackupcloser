# ZxyBackupCloser

_ZxyBackupCloser_ is an **easy backup application** to store your ZFS pools containing a lot of snapshots to another ZFS pool or dataset.

Patineboot is backing up all Patineboot's ZFS pools on internal SSDs to an external SSD with _ZxyBackupCloser_ every time.

## Feature

You back up your ZFS pools with the one command, only _ZxyBackupCloser_.

- _ZxyBackupCloser_ keeps all of the snapshots of your ZFS pools in the backup ZFS pools.
- _ZxyBackupCloser_ supports the incremental backup from the previous backup.
- _ZxyBackupCloser_ verifies the original and the backup ZFS pools with the portable mac.
- _ZxyBackupCloser_ gets the difference between the previous and the present backup ZFS pools.

## Official Web Site

Official Release: <https://pypi.org/project/zxybackupcloser/>

Official Development Site: <https://github.com/patineboot/zxybackupcloser>

## Install _ZxyBackupCloser_ (Recommend)

1. Install _ZxyBackupCloser_ from PyPI.

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

- [_ZxybackupCloser_](https://github.com/patineboot/zxybackupcloser)
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

e.g., Patineboot backs up two of the original pools named _home.pool_ and _storage.pool_ to the _backup.pool_ pool.

```bash
sudo zxybackupcloser -b backup.pool home.pool storage.pool
```

_Warn_: Remove the com.sun:auto-snapshot property on the backup pool, or taking snapshots disturb the backup process.

Remove the com.sun:auto-snapshot property:

```bash
sudo zfs set com.sun:auto-snapshot=false <backup pool>
```

### Advanced Usage

See more detail of usage, run the `zxybackupcloser` command with the `-h` option.

```bash
$ zxybackupcloser -h

usage: zxybackupcloser [-h] -b BACKUP [-d] [-v] [-n] [-u] pool [pool ...]

_ZxyBackupCloser_ is a backup application to back up some ZFS pools to another ZFS pool or dataset.

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

### Helpful Tool

Patineboot has two helpful tools in the _misc_ directory.

- _zfs-load-enckey.service_  
   Load the encryption key and mount filesystems automatically on the booting of your machine.
- *zxycloser_warapper.sh*  
   Fulfill Patineboot's pools and verify the backup automatically.

## Install and run _ZxyBackupCloser_ from GitHub

1. Get _ZxyBackupCloser_ from GitHub.com

   Get _ZxyBackupCloser_ with `git clone`:

   ```bash
   git clone https://github.com/patineboot/zxybackupcloser.git
   ```

2. Run the `backupcloser.py` script

   Move the current directory to the script directory by `cd zxybackupcloser/src/zxybackupcloser` and run the `backupcloser.py` script:

   ```bash
   cd ./zxybackupcloser/src/zxybackupcloser
   sudo ./backupcloser.py -h
   ```

## Configure _ZxyBackupCloser_

Patineboot prepared the macros for deep configuration on the _backupcloser.py_ script file.
Change the macros for taking the snapshots and logging while backing up.

Notice: you can find the place of the _backupcloser.py_ file with `pip3 show zxybackupcloser`.

## Environment

Patineboot is running _ZxyBackupCloser_ with the following software environment.
_ZxyBackupCloser_ can run with other software or versions.

OS: Ubuntu Server 22.04

- Python 3.10.4
- ZFS on Linux 2.1.2
- pv 1.6.6
- zfs-auto-snapshot 1.2.4

## Deploy _ZxyBackupCloser_ for Patineboot's development

Run _ZxyBackupCloser_ while developing:

```bash
sudo PYTHONPATH=../ ./backupcloser.py -b <backup pool> <original pools>
```

Deploy _ZxyBackupCloser_ on PyPI:

```bash
python3 -m build
python3 -m twine upload dist/*
```

twine asks:

```bash
User: patineboot
Pass: <your passphrase>
```

Update _ZxyBackupCloser_ from PyPI.

   Update `zxybackupcloser` with the `pip3` command.

   ```bash
   pip3 install -U zxybackupcloser
   ```

Reference: [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
