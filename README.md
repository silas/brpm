brpm
====

brpm is a simple tool for building RPMs.

### Usage

Build spec files in the current working directory for the arch and dist of the
build machine:

    brpm

Build `python-gevent.spec` for Fedora 16 i386 and x86\_64:

    brpm --dist=fedora-16 --arch=i386,x86_64 ./python-gevent.spec

If we have a `build.json` file which looks something like:

    [
      {"spec": "python-asyncmongo/python-asyncmongo.spec"},
      {"spec": "python-gevent/python-gevent.spec"},
      {"spec": "python-redis/python-redis.spec"}
    ]

We can build all those RPMs with the following command:

    brpm ./build.json

Or just those starting at `python-gevent`:

    brpm ./build.json --start=python-gevent

Or only `python-redis`:

    brpm ./build.json --only=python-redis

### Directory Layout

Lets say we have the following directory structure:

    [silas@x201 rpm]$ tree
    .
    └── python-huck
        └── python-huck.spec

        1 directory, 1 file

We `cd` into `python-huck` and run a build:

    [silas@x201 rpm]$ cd python-huck
    [silas@x201 python-huck]$ brpm
    INFO:root:Building python-huck
    INFO:root:Retrieving source http://pypi.python.org/packages/source/h/huck/huck-0.1.0.tar.bz2

And `cd` back to `rpm` and run `tree` again:

    [silas@x201 python-huck]$ cd ..
    [silas@x201 rpm]$ tree
    .
    ├── build
    │   └── fedora
    │       └── 14
    │           ├── SRPMS
    │           │   ├── python-huck-0.1.0-1.fc14.src.rpm
    │           │   └── repodata
    │           │       ├── filelists.xml.gz
    │           │       ├── other.xml.gz
    │           │       ├── primary.xml.gz
    │           │       └── repomd.xml
    │           └── x86_64
    │               ├── python-huck-0.1.0-1.fc14.noarch.rpm
    │               └── repodata
    │                   ├── filelists.xml.gz
    │                   ├── other.xml.gz
    │                   ├── primary.xml.gz
    │                   └── repomd.xml
    └── python-huck
        ├── build
        │   ├── build.log
        │   ├── root.log
        │   └── state.log
        ├── huck-0.1.0.tar.bz2
        └── python-huck.spec

    9 directories, 15 files

### Requirements

* Python >= 2.6
* [createrepo](https://admin.fedoraproject.org/pkgdb/acls/name/createrepo)
* [curl](https://admin.fedoraproject.org/pkgdb/acls/name/curl)
* [mock](https://admin.fedoraproject.org/pkgdb/acls/name/mock)
* [ops](https://github.com/silas/ops)
* [rpmbuild](https://admin.fedoraproject.org/pkgdb/acls/name/rpm)

### Licenses

This work is licensed under the MIT License (see the LICENSE file).
