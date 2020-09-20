#!/usr/bin/python

from setuptools import setup
import os

data_dirs = {'tex': '/pylink/tex'}

cur_dir = os.path.dirname(os.path.realpath(__file__))

data_files = []

with open(os.path.join(cur_dir, 'README.md'), 'r') as fh:
    long_description = fh.read()

for srcdir, dst in data_dirs.items():
    srcpath = os.path.join(cur_dir, srcdir)
    files = [os.path.join(srcdir, f) for f in os.listdir(srcpath)]
    data_files.append((dst, files,))

setup(
    name='pylink-satcom',
    version='0.8',
    author='Harrison Caudill',
    author_email='harrison@hypersphere.org',
    description='Python Link Budget System',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/harrison-caudill/pylink',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Ham Radio',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: Physics',
        ],
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
    packages=[
        'pylink',
        'pylink.tributaries'
        ]
    )
