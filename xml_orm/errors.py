#!/usr/bin/env python
#-*- coding: utf-8 -*-


class XML_ORM_Error(Exception):
    pass


class DefinitionError(XML_ORM_Error):
    pass


class ValidationError(XML_ORM_Error):
    pass


class SerializationError(XML_ORM_Error):
    pass
