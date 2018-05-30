#!/usr/bin/env python

import os
import sys

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# 'setup.py publish' shortcut.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine upload dist/*')
    sys.exit()

packages = ['opsparkctl']

about = {}
with open(os.path.join(here, 'opsparkctl', '__version__.py'), 'r') as f:
    exec(f.read(), about)

with open(os.path.join(here, 'opsparkctl', 'README.rst'), 'r') as f:
    readme = f.read()

requires = [
    'python>=2.7.5',
    'python-magnumclient>=2.7.0', # Apache-2.0
    'qprompt>=0.9.7',
    'python-novaclient>=9.1.1',
    'keystoneauth1>=3.3.0',
    'python-keystoneclient>=3.8.0',
    'keystoneauth1[kerberos]',
    'kubernetes==6.0.0'
]

try:
    import ssl
except ImportError:
    requires.append('ssl')

if sys.version_info < (2,7):
    sys.exit('Sorry, Python < 2.7 is not supported')

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=packages,
    entry_points={
        'console_scripts': [
            'opsparkctl = opsparkctl.shell:main',
        ],
    },
    include_package_data=True,
    python_requires=about['__python_requires__'],
    install_requires=requires,
    license=about['__license__'],
    zip_safe=False,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ),
    extras_require={
    },
)