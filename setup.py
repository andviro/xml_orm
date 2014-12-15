#!/usr/bin/env python
#-*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys

try:
    from setuptools import setup
    has_setuptools = True
except ImportError:
    from distutils.core import setup
    has_setuptools = False


setup_params = dict(name='xml_orm',
                    version='0.6.14',
                    packages=[str('xml_orm')],
                    author='Andrew Rodionoff',
                    author_email='andviro@gmail.com',
                    license='LGPL',
                    description='Yet another XML to python object mapping, a la Django ORM',
                    )

if has_setuptools:
    setup_params.update({
        'entry_points': {
            'console_scripts': [
                'xsdinspect=xml_orm.inspect:main',
                'xsdinspect-%s.%s=xml_orm.inspect:main' % sys.version_info[:2]
            ],
        },
        'zip_safe': False,
        'setup_requires' : ['nose', 'coverage'],
    })
else:
    if sys.platform == 'win32':
        print('Warning: not creating exe file')
    setup_params['scripts'] = ['scripts/xsdinspect']

setup(**setup_params)
