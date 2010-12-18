import fnmatch
import glob
import logging
import os
import ops.utils

logging.basicConfig(level=logging.INFO)

class Break(Exception): pass

class Build(object):

    def __init__(self, options, data):
        self.options = options
        self.spec_path = data['spec']
        self.root_path = os.path.dirname(self.spec_path)
        self.build_path = os.path.join(self.root_path, 'build')
        self.repo_path = os.path.dirname(self.root_path)

    def run(self):
        ops.utils.rm(self.build_path, recursive=True)
        ops.utils.mkdir(self.build_path)

        # Build RPMs
        for arch in ['srpms'] + self.options.arch:
            path = os.path.join(self.repo_path, 'build', arch)
            ops.utils.mkdir(path)
            if not os.path.exists(os.path.join(path, 'repodata')):
                ops.utils.run('createrepo --update ${dst}', dst=path)

        # Build SRPM
        result = self.srpm()
        if result:
            self.srpm_path = result.stdout.strip()[7:]
        else:
            ops.utils.exit(code=result.code, text=result.stderr)

        srpm_dst_path = os.path.join(self.repo_path, 'build', 'srpms')

        # Build RPMs
        for arch in self.options.arch:
            result = self.rpm(arch)
            if not result:
                ops.utils.exit(code=result.code, text=result.stderr)
            arch_dst_path = os.path.join(self.repo_path, 'build', arch)
            ops.utils.mkdir(arch_dst_path)
            # TODO(silas):  don't build multiple times on noarch
            ops.utils.run('mv ${src}/*.noarch.rpm ${dst}', src=self.build_path, dst=arch_dst_path)
            ops.utils.run('mv ${src}/*${arch}.rpm ${dst}', src=self.build_path, arch=arch, dst=arch_dst_path)
            ops.utils.run('mv ${src}/*.el5.src.rpm ${dst}', src=self.build_path, dst=srpm_dst_path)
            ops.utils.run('createrepo --update ${dst}', dst=arch_dst_path)

    def srpm(self):
        command = 'rpmbuild'
        if self.options.dist == 'epel-5':
            command += ' --define "_source_filedigest_algorithm=1"'
        command += ' --define "_sourcedir ${root_path}"'
        command += ' --define "_specdir ${root_path}"'
        command += ' --define "_srcrpmdir ${build_path}"'
        command += ' -bs --nodeps "${spec_path}"'
        return ops.utils.run(
            command,
            build_path=self.build_path,
            spec_path=self.spec_path,
            root_path=self.root_path,
        )

    def rpm(self, arch):
        command = 'mock -vr ${dist}-${arch}'
        command += ' --resultdir=${build_path}'
        command += ' ${srpm_path}'
        if self.options.no_clean:
            command += ' --no-clean'
        return ops.utils.run(
            command,
            dist=self.options.dist,
            arch=arch,
            build_path=self.build_path,
            srpm_path=self.srpm_path,
        )

def main():
    import json
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

    arch = ops.utils.run('uname -m').stdout.strip()
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
        '--start',
        dest='start',
        help='start building with PACKAGE',
        metavar='PACKAGE',
    )
    parser.add_option(
        '--only',
        dest='only',
        help='build only PACKAGE',
        metavar='PACKAGE',
    )
    parser.add_option(
        '--arch',
        dest='arch',
        default=arch,
        help='comma separated list of architectures (%s)' % arch,
        metavar='ARCH',
    )
    parser.add_option(
        '--no-clean',
        dest='no_clean',
        action='store_true',
        help='don\'t clean up before build',
    )
    options, args = parser.parse_args()

    if not args:
        args = glob.glob('*.spec')

    if not args:
        ops.utils.exit(code=1, text='File required')

    if not options.dist:
        ops.utils.exit(code=1, text='Dist option is required')

    if not options.arch:
        ops.utils.exit(code=1, text='Architecture is required')
    else:
        options.arch = [arch.strip() for arch in options.arch.split(',')]
        if '' in options.arch:
            options.arch.remove('')

    build_list = []

    for path in args:
        path = os.path.realpath(path)
        if not os.path.isfile(path):
            ops.utils.exit(code=1, text='File not found: %s' % path)
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
                ops.utils.exit(code=1, text='Invalid json syntax')
            except Exception, error:
                ops.utils.exit(code=1, text='Invalid build file (%s)' % error)
        elif fnmatch.fnmatch(path, '*.spec'):
            build_list.append({'spec': os.path.realpath(path)})
        else:
            ops.utils.exit(code=1, text='Unknown file type: %s' % path)

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
            print '%s\n%s' % ('#'*80, package)
            Build(options, data).run()
        except Break:
            pass
