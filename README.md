# XML ORM -- XML document to Python object mapping

This library is inspired by Django object to relation
[layer](https://docs.djangoproject.com/en/dev/topics/db/models/). XML document 
schemas are represented by Python classes with fields corresponding to nested 
elements and attributes. Document namespaces and encodings are stored as class 
Meta information. Object instances are transparently loaded from XML documents, 
with validation on load and save operations. Object-oriented approach allows 
reusing of schema elements by inheritance and overriding of XML elements and 
attributes represented by Python class members. XML namespaces, serialization 
an de-serialization to different encodings and optional schema validation are 
supported, along with most common XSD types to Python objects mapping. XSD 
inspection utility is provided for conversion of existing XSD schemas to Python 
objects (very much work in progress, but usable for simple schemas). 
Documentation is work in progress, mostly in Russian. For reference see source 
of `test.py` which showcases all current features.
