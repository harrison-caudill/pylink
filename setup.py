#!/usr/bin/python

from setuptools import setup
import os
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

packages = ['pylink']
data_dirs = {'tex': '/usr/local/share/pylink'}

cur_dir = os.path.dirname(os.path.realpath(__file__))

data_files = []

for srcdir, dst in data_dirs.iteritems():
    srcpath = os.path.join(cur_dir, srcdir)
    files = [os.path.join(srcdir, f) for f in os.listdir(srcpath)]
    data_files.append((dst, files,))

deps = 'jinja2'
        
setup(name='pylink',
      version='0.3',
      description='Python Link Budget System',
      author='Harrison Caudill',
      author_email='harrison@hypersphere.org',
      packages=packages,
      data_files=data_files,
      install_requires=reqs,)
