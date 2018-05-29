import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests/', '-s', '--junitxml', 'unittest.xml']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='n_property',
    version='0.0.5',
    author='hrmthw,yetone',
    description='To solve the N+1 problem of @property.',
    url='https://github.com/hrmthw/n_property',
    packages=find_packages(exclude=['tests.*', 'tests'],),
    test_suite='tests',
    cmdclass={'test': PyTest},
    tests_require=(
        'pytest',
    )
)
