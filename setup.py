#!/usr/bin/env python

from distutils.core import setup
import sys
sys.path.append('GDSLatexConverter')
from GDSLatexConverter import GDSLatexConverter
     
from setuptools import setup, find_packages
from distutils.version import StrictVersion
from importlib import import_module
import re


def get_version(verbose=1):
    v = GDSLatexConverter.GDSLatexConverter.__version__
    if verbose:
        print(v)
    return v


def readme():
    with open('README.md') as f:
        return f.read()


def license():
    with open('LICENSE') as f:
        return f.read()

setup(name='GDSLatexConverter',
      version=get_version(),
      use_2to3=False,
      author='René Vollmer',
      author_email='admin@aypac.de',
      maintainer='René Vollmer',
      maintainer_email='admin@aypac.de',
      description='GDS to latex pdf converter',
      # long_description=readme(),
      url='https://github.com/Aypac/GDSLatexConverter',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers'
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.6',
          'Topic :: Scientific/Engineering'
      ],
      # license=license(),
      # if we want to install without tests:
      # packages=find_packages(exclude=["*.tests", "tests"]),
      packages=['GDSLatexConverter', ],
      install_requires=[
          'gdspy>=1.2',
          'numpy>=1.13.3',
          ],
      # 're>=2.2.1' is a standard part of python
      # test_suite='pyqip.tests',
zip_safe=False)
