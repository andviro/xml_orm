#!/usr/bin/env python
#-*- coding: utf-8 -*-

from .pfr import ContainerPFR
from .fns import ContainerFNS
from .edi import ContainerEDI
from .stat import ContainerStat

import re
import os

#Маска                     направление                 код протокола
# FNS_*                            ФНС                                7
# EDI_*                             ЭСФ                               20
# r'stat' icase                   РосСТат                            4
# r'\d{3}-\d{3}-\d{6}_'            ПФР                               2
# SOS_*                           ЕГР 1С                          25


def autoload(fn, content=None):
    u'''
    Автоопределение типа контейнера по имени файла.

    :fn: путь к файлу (в него будет сохраняться контейнер!)
    :content: необязательный источник загрузки. Может быть файловым объектом
        или байтовой строкой. Если источник не указан, загрузка производится из
        файла на диске по имени :fn:.

    '''
    base, fn = os.path.split(os.path.abspath(fn))
    if fn.startswith('FNS_'):
        res = ContainerFNS.load(content or fn)
    elif fn.startswith('EDI_'):
        res = ContainerEDI.load(content or fn)
    elif re.match(r'\d{3}-\d{3}(-\d{6})?_.*', fn):
        res = ContainerPFR.load(content or fn)
    elif fn.lower().startswith('stat'):
        res = ContainerStat.load(content or fn)
    else:
        res = None
    if res:
        res.package = fn
        res.basedir = base
    return res
