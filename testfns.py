#!/usr/bin/env python
#-*- coding: utf-8 -*-

from uuid import uuid4
from containers.fns import ContainerFNS

# �������� ���������� "� ����"
# � ���������� ������������ ����� ���������� ��������� �������� �����
# ��� ������������ ����� ������������� �������� �� ���������
# ������������� ���� ��� ��������� ������ ���������� ��� ������� �������
# .save() ��� ������������� ��������� � XML.
ti = ContainerFNS(uid=uuid4().hex)
ti.sender = ContainerFNS.Sender(uid=uuid4().hex)
ti.receiver = ti.Receiver(uid=uuid4().hex)
ti.sos = ti.Sos(uid=u'2AE')
for n in range(3):
    uid = uuid4().hex
    doc = ti.Doc(
        uid=uid,
        orig_filename=uid + '.xml',
        content=ti.Doc.Content(filename=(uid + '.bin')))
    print unicode(doc)
    # ���������� ����������� ��������� � ����������� ����������
    ti.doc.append(doc)
    # ���������� ���������� ����� � ����������� ����������
    ti.add_file(doc.content.filename, 'test document content')
    for k in range(2):
        sig = doc.Signature(filename=(uuid4().hex + '.bin'))
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
