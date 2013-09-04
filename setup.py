#!/usr/bin/env python
#-*- coding: utf-8 -*-

from distutils.core import setup


setup(name='xml_orm',
      version='0.6.1',
      packages=['xml_orm'],
      scripts=['inspector.py'],
      author='Andrew Rodionoff',
      author_email='andviro@gmail.com',
      license='LGPL',
      description='Yet another XML to python object mapping, a la Django ORM',
      )
