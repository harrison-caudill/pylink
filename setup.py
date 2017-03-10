#!/usr/bin/python

from distutils.core import setup
import os
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

data_dirs = {'tex': '/usr/local/share/pylink'}

cur_dir = os.path.dirname(os.path.realpath(__file__))

data_files = []

for srcdir, dst in data_dirs.iteritems():
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
      package_dir={
          'tributaries':'tributaries',
          },
      packages=['pylink', 'pylink.tributaries'])
#install_requires=reqs,)
