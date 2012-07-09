# Copyright (c) 2011, Silas Sewell
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

import fnmatch
import glob
import json
import logging as log
import ops
import os
import rpm

log.basicConfig(level=log.INFO)

class Break(Exception): pass

class Build(object):

    def __init__(self, options, data):
        self.options = options
        self.dist_name, self.dist_version = options.dist.split('-')
        self.spec_path = data['spec']
        self.root_path = os.path.dirname(self.spec_path)
        self.build_path = os.path.join(self.root_path, 'build')
        self.repo_path = os.path.dirname(self.root_path)
        self.ops_run = dict(stdout=True, stderr=True)
        try:
            self.rpm_spec = rpm.ts().parseSpec(self.spec_path)
        except Exception, error:
            log.error('Unable to parse spec file: %s' % self.spec_path)
            self.rpm_spec = None

    def run(self):
        if os.path.exists(self.build_path):
            ops.rm(self.build_path, recursive=True)
        ops.mkdir(self.build_path)

        # Build repository directories
        for arch in ['SRPMS'] + self.options.arch:
            path = os.path.join(self.repo_path, 'build', self.dist_name, self.dist_version, arch)
            ops.mkdir(path)
            if not os.path.exists(os.path.join(path, 'repodata')):
                ops.run('createrepo --update ${dst}', dst=path, **self.ops_run)

        # Try to get source files if they don't exist locally
        self.sources()

        # Build SRPM
        result = self.srpm()
        if result:
            self.srpm_path = result.stdout.strip()[7:]
        else:
            ops.exit(code=result.code)

        srpm_dst_path = os.path.join(self.repo_path, 'build', self.dist_name, self.dist_version, 'SRPMS')

        # Build RPMs
        for arch in self.options.arch:
            result = self.rpm(arch)
            if not result:
                ops.exit(code=result.code, text=result.stderr)
            arch_dst_path = os.path.join(self.repo_path, 'build', self.dist_name, self.dist_version, arch)
            ops.mkdir(arch_dst_path)
            # TODO(silas):  don't build multiple times on noarch
            ops.run('mv ${src}/*.noarch.rpm ${dst}', src=self.build_path, dst=arch_dst_path, **self.ops_run)
            arch_list = [arch]
            if arch == 'i386':
                arch_list.append('i686')
            for a in arch_list:
                ops.run('mv ${src}/*${arch}.rpm ${dst}', src=self.build_path, arch=a, dst=arch_dst_path, **self.ops_run)
            # Find and move distribution srpm
            srpms = glob.glob(os.path.join(self.build_path, '*.src.rpm'))
            srpms = [os.path.basename(path) for path in srpms]
            srpm_name = os.path.basename(self.srpm_path)
            if srpm_name in srpms:
                srpms.remove(srpm_name)
            srpm_path = os.path.join(self.build_path, srpms[0]) if srpms else self.srpm_path
            ops.run('mv ${src} ${dst}', src=srpm_path, dst=srpm_dst_path, **self.ops_run)
            # Update repository
            ops.run('createrepo --update ${dst}', dst=arch_dst_path, **self.ops_run)

    def sources(self):
        if self.rpm_spec:
            for src, _, _ in self.rpm_spec.sources:
                name = None
                for value in ('http://', 'https://', 'ftp://'):
                    if src.startswith(value):
                        dst = os.path.join(self.root_path, src.split('/')[-1])
                        if not os.path.exists(dst):
                            log.info('Retrieving source %s' % src)
                            ops.run('curl -sL ${src} > ${dst}', src=src, dst=dst, **self.ops_run)

    def srpm(self):
        command = 'rpmbuild'
        if self.options.dist == 'epel-5':
            command += ' --define "_source_filedigest_algorithm=1"'
        command += ' --define "_sourcedir ${root_path}"'
        command += ' --define "_specdir ${root_path}"'
        command += ' --define "_srcrpmdir ${build_path}"'
        command += ' -bs --nodeps "${spec_path}"'
        return ops.run(
            command,
            build_path=self.build_path,
            spec_path=self.spec_path,
            root_path=self.root_path,
            **self.ops_run
        )

    def rpm(self, arch):
        command = 'mock -vr ${dist}-${arch}'
        command += ' --resultdir=${build_path}'
        command += ' ${srpm_path}'
        return ops.run(
            command,
            dist=self.options.dist,
            arch=arch,
            build_path=self.build_path,
            srpm_path=self.srpm_path,
            **self.ops_run
        )


def build(file_list, options):
    build_list = []

    for path in file_list:
        path = os.path.realpath(path)
        if os.path.isdir(path):
            file_list += glob.glob('*.spec')
            continue
        elif not os.path.isfile(path):
            ops.exit(code=1, text='File not found: %s' % path)
        if fnmatch.fnmatch(path, '*.json'):
            try:
                with open(path) as f:
                    bl = json.loads(f.read())
                if not isinstance(bl, list):
                    raise Exception()
                root_path = os.path.dirname(path)
                for data in bl:
                    data['spec'] = os.path.realpath(os.path.join(root_path, data['spec']))
                build_list += bl
            except ValueError:
                ops.exit(code=1, text='Invalid json syntax')
            except Exception, error:
                ops.exit(code=1, text='Invalid build file (%s)' % error)
        elif fnmatch.fnmatch(path, '*.spec'):
            build_list.append({'spec': os.path.realpath(path)})
        else:
            ops.exit(code=1, text='Unknown file type: %s' % path)

    if not build_list:
        ops.exit(code=1, text='Nothing to build')

    for data in build_list:
        try:
            package = os.path.basename(data['spec'])[:-5]
            if options.only:
                if options.only != package:
                    continue
            elif options.start:
                if options.start == package:
                    options.start = ''
                else:
                    continue
            log.info('Building %s' % package)
            Build(options, data).run()
        except Break:
            pass

def run():
    import optparse

    release = {
        '/etc/fedora-release': 'fedora',
        '/etc/redhat-release': 'epel',
    }

    dist = ''
    for path, name in release.items():
        if os.path.isfile(path) and not os.path.islink(path):
            with open(path) as f:
                version = f.read().split()[2].partition('.')[0]
                dist = '%s-%s' % (name, version)
                break

    arch = ops.run('uname -m').stdout.strip()
    if arch != 'x86_64':
        arch == 'i386'

    usage = 'Usage: %prog [options] file...'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        '-d',
        '--dist',
        dest='dist',
        help='distribution' + ' (%s)' % dist if dist else '',
        default=dist,
        metavar='DIST',
    )
    parser.add_option(
        '-s',
        '--start',
        dest='start',
        help='start building with PACKAGE',
        metavar='PACKAGE',
    )
    parser.add_option(
        '-o',
        '--only',
        dest='only',
        help='build only PACKAGE',
        metavar='PACKAGE',
    )
    parser.add_option(
        '-a',
        '--arch',
        dest='arch',
        default=arch,
        help='comma separated list of architectures (%s)' % arch,
        metavar='ARCH',
    )
    options, args = parser.parse_args()

    if not args:
        args = ['.']

    if not options.dist:
        ops.exit(code=1, text='Dist option is required')

    if not options.arch:
        ops.exit(code=1, text='Arch is required')
    else:
        options.arch = [arch.strip() for arch in options.arch.split(',')]
        if '' in options.arch:
            options.arch.remove('')

    build(args, options)

if __name__ == '__main__':
    run()
