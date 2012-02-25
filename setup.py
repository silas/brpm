from distutils.core import setup

setup(
    name='brpm',
    version='0.2.0',
    description='A tool for building RPM packages',
    long_description='brpm is a simple tool for building RPMs.',
    author='Silas Sewell',
    author_email='silas@sewell.org',
    license='MIT License',
    url='https://github.com/silas/brpm',
    packages=['brpm'],
    scripts=['brpm'],
)
