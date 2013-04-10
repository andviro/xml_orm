#!/usr/bin/env python
#-*- coding: utf-8 -*-

from .pfr import *
from .fns import *
from .stat import *

import re
import os

#Маска                     направление                 код протокола
# FNS_*                            ФНС                                7
# EDI_*                             ЭСФ                               20
# r'stat' icase                   РосСТат                            4
# r'\d{3}-\d{3}-\d{6}_'            ПФР                               2
# SOS_*                           ЕГР 1С                          25


def autoload(fn):
    base = os.path.basename(fn)
    if base.startswith('FNS_'):
        return ContainerFNS.load(fn)
    elif re.match(r'\d{3}-\d{3}-\d{6}_.*', base):
        return ContainerPFR.load(fn)
    elif base.lower().startswith('stat'):
        return ContainerStat.load(fn)
    else:
        return None
