#!/usr/bin/env python
#-*- coding: utf-8 -*-
from containers.pfr import *

def main():
    # �������� ���������� "� ����"
    # � ���������� ������������ ����� ���������� ��������� �������� �����
    # ��� ������������ ����� ������������� �������� �� ���������
    # ������������� ���� ��� ��������� ������ ���������� ��� ������� �������
    # .save() ��� ������������� ��������� � XML.
    ti = ContainerPFR(uid=uuid4().hex)
    ti.sender = PFRSender(uid=uuid4().hex)
    ti.receiver = PFRReceiver(uid=uuid4().hex)
    ti.sos = SOS(uid=u'2AE')
    for n in range(3):
        doc = Document()
        doc.uid = uuid4().hex
        doc.orig_filename = doc.uid + '.xml'
        doc.content = Content(filename=(doc.uid + '.bin'))
        # ���������� ����������� ��������� � ����������� ����������
        ti.document.append(doc)
        # ���������� ���������� ����� � ����������� ����������
        ti.add_file(doc.content.filename, 'test document content')
        for k in range(2):
            sig = Signature(filename=(uuid4().hex + '.bin'))
            # ���������� ����������� ������� � ����������� ���������
            doc.signature.append(sig)
            # ���������� ����� ������� � ����������� ����������
            ti.add_file(sig.filename, 'test signature content')
    print ti
    pass

if __name__ == "__main__":
    main()

