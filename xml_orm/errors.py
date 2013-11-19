#!/usr/bin/env python
#-*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function


class XML_ORM_Error(Exception):
    pass


class DefinitionError(XML_ORM_Error):
    pass


class ValidationError(XML_ORM_Error):
    pass


class SerializationError(XML_ORM_Error):
    pass
