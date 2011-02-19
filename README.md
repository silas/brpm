brpm
====

brpm is a simple tool that makes building RPMs locally a little easier.

### Usage

Build spec files in the current working directory for the arch and dist of the
build machine:

    brpm

Build `file.spec` for Fedora 13 i386 and x86\_64:

    brpm --dist=fedora-13 --arch=i386,x86_64 ./python-gevent.spec

Where `build.json` looks something like:

    [
      {"spec": "python-asyncmongo/python-asyncmongo.spec"},
      {"spec": "python-gevent/python-gevent.spec"},
      {"spec": "python-redis/python-redis.spec"}
    ]

Build all RPMs:

    brpm ./build.json

Build all RPMs starting from `python-gevent`:

    brpm ./build.json --start=python-gevent

Build only `python-redis`:

    brpm ./build.json --only=python-redis

### Requirements

* Python >= 2.6
* [createrepo](https://admin.fedoraproject.org/pkgdb/acls/name/createrepo)
* [curl](https://admin.fedoraproject.org/pkgdb/acls/name/curl)
* [mock](https://admin.fedoraproject.org/pkgdb/acls/name/mock)
* [ops](https://github.com/opsdojo/ops)
* [rpmbuild](https://admin.fedoraproject.org/pkgdb/acls/name/rpm)

### Licenses

This work is licensed under the MIT License (see the LICENSE file).
