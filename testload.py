#!/usr/bin/env python
#-*- coding: utf-8 -*-

from glob import iglob
from schemas.auto import autoload


def main():
    for fn in iglob('tmp/*.zip'):
        print fn
        print unicode(autoload(fn))


if __name__ == "__main__":
    main()
