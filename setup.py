from distutils.core import setup

long_description = """
brpm is a simple tool that makes building RPMs locally a little easier.
"""

setup(
    name='brpm',
    version='0.1.0',
    description='A tool for building RPM packages',
    long_description=long_description.strip(),
    author='Silas Sewell',
    author_email='silas@sewell.ch',
    license='MIT License',
    url='https://github.com/silas/brpm',
    packages=['brpm'],
    scripts=['scripts/brpm'],
)
