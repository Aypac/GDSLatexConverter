#!/usr/bin/env python

__version__ = '0.14'

import sys
import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='GDSLatexConverter',
      version=__version__,
      use_2to3=False,
      author='Rene Vollmer',
      author_email='admin@aypac.de',
      maintainer='Rene Vollmer',
      maintainer_email='admin@aypac.de',
      description='GDS to latex pdf converter',
      long_description=read('README.md'),
      url='https://github.com/Aypac/GDSLatexConverter',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers'
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.6.0',
          'Programming Language :: Python :: 3.6.2',
          'Topic :: Scientific/Engineering',
      ],
      # license=read('LICENCE'),
      # if we want to install without tests:
      # packages=find_packages(exclude=["*.tests", "tests"]),
      #packages=find_packages(),
      packages=['GDSLatexConverter', ],
      install_requires=[
          'gdspy==1.4.1',
          'numpy>=1.13.3',
          ],
      # 're>=2.2.1' is a standard part of python
      # test_suite='pyqip.tests',
      zip_safe=False,
)
