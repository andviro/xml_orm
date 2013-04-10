#!/usr/bin/env python
#-*- coding: utf-8 -*-

from containers.fns import *

# �������� ���������� "� ����"
# � ���������� ������������ ����� ���������� ��������� �������� �����
# ��� ������������ ����� ������������� �������� �� ���������
# ������������� ���� ��� ��������� ������ ���������� ��� ������� �������
# .save() ��� ������������� ��������� � XML.
ti = ContainerFNS(uid=uuid4().hex)
ti.sender = Sender(uid=uuid4().hex)
ti.receiver = Receiver(uid=uuid4().hex)
ti.sos = SOS(uid=u'2AE')
for n in range(3):
    doc = Document()
    doc.uid = uuid4().hex
    doc.orig_filename = doc.uid + '.xml'
    doc.content = Content(filename=(doc.uid + '.bin'))
    # ���������� ����������� ��������� � ����������� ����������
    ti.files.append(doc)
    # ���������� ���������� ����� � ����������� ����������
    ti.add_file(doc.content.filename, 'test document content')
    for k in range(2):
        sig = Signature(filename=(uuid4().hex + '.bin'))
        # ���������� ����������� ������� � ����������� ���������
        doc.signature.append(sig)
        # ���������� ����� ������� � ����������� ����������
        ti.add_file(sig.filename, 'test signature content')

# ���������� ���������, ������ ���� ��������� ����������� ���������
ti.save()
print ti.package
# �������� ���������� �� ����� ������������ �� �����, ���� �� ��������
# ������ �����������, ���� �� ��������� ��������� �������
with ContainerFNS.load(ti.package) as newti:
    # ���������� � ��������� ��������� ��������� �� �����������
    # ���������� ������
    newti.add_file('lalalala', 'lalalala')
    # ���� �� �������� ���� 'package', ���� ������ ����������� ��������
    # ����������� ����. ��� ����� ��������� ����������� ��� ����
    # ������, � ��� ������ ����������� �������������.
    newti.package = 'some_other.zip'
    # ����� �� ��������� ��������� �����
