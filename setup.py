#!/usr/bin/python

from setuptools import setup
import os

data_dirs = {'tex': '/pylink/tex'}

cur_dir = os.path.dirname(os.path.realpath(__file__))

data_files = []

for srcdir, dst in data_dirs.items():
    srcpath = os.path.join(cur_dir, srcdir)
    files = [os.path.join(srcdir, f) for f in os.listdir(srcpath)]
    data_files.append((dst, files,))

setup(name='pylink',
      version='0.3',
      description='Python Link Budget System',
      author='Harrison Caudill',
      author_email='harrison@hypersphere.org',
      license='BSD',
      data_files=data_files,
      install_requires=[
          'matplotlib',
          'jinja2',
          'scipy',
          'numpy',
          ],
      package_dir={
          'tributaries':'tributaries',
          },
      packages=['pylink', 'pylink.tributaries'])

