#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from xml.dom.minidom import parse

tpl = """# -*- coding: utf-8 -*-

import os.path
from mimetypes import types_map

DEFAULT_MIME_TYPE = "application/octet-stream"

class MimeType(object):
	_mimes_map = %r
	_types_map = types_map
	
	def __init__(self, mime):
		if mime not in self._mimes_map:
			mime = DEFAULT_MIME_TYPE
		self.__name = mime
	
	@classmethod
	def fromName(cls, f):
		_, ext = os.path.splitext(f)
		if ext not in cls._types_map: # Always try a case-sensitive match first
			ext = ext.lower()
		if ext in cls._types_map:
			mime = cls._types_map[ext]
		else:
			mime = DEFAULT_MIME_TYPE
		return cls(mime)
	
	@classmethod
	def register(cls, mime, extension, parent="", comment="", icon=""):
		cls._mimes_map[mime] = (parent, comment, icon)
		cls._types_map[extension] = mime
	
	@classmethod
	def registerExtension(cls, mime, extension):
		cls._types_map[extension] = mime
	
	def comment(self):
		return self._mimes_map[self.name()][1]
	
	def genericIcon(self):
		return self._mimes_map[self.name()][2]
	
	def icon(self):
		return self.genericIcon() or self.name().replace("/", "-")
	
	def isDefault(self):
		return self.name() is DEFAULT_MIME_TYPE
	
	def name(self):
		return self.__name
	
	def parent(self):
		parent = self._mimes_map[self.name()][0]
		return MimeType(parent)

del types_map
assert DEFAULT_MIME_TYPE in MimeType._mimes_map

MimeType.register("application/vnd.bliz-anim", ".anim", "", "Model ANIM data",    "3d-x-generic")
MimeType.register("application/vnd.bliz-dbc",  ".dbc",  "", "WoW database file",  "x-office-spreadsheet")
MimeType.register("application/vnd.bliz-mdx",  ".mdx",  "", "Blizzard MDX model", "3d-x-generic")
MimeType.register("application/vnd.bliz-mpq",  ".mpq",  "", "MPQ archive",        "package-x-generic")
MimeType.register("application/vnd.bliz-skin", ".skin", "", "Model SKIN data",    "3d-x-generic")
MimeType.register("application/vnd.bliz-wmo",  ".wmo",  "", "World model object", "3d-x-generic")
MimeType.register("image/vnd.bliz-blp",        ".blp",  "", "BLP image",          "image-x-generic")
MimeType.registerExtension("application/vnd.bliz-dbc", ".db2")
MimeType.registerExtension("application/vnd.bliz-dbc", ".wdb")
MimeType.registerExtension("application/vnd.bliz-mdx", ".mdx")
MimeType.registerExtension("application/vnd.bliz-mdx", ".m2")
MimeType.registerExtension("application/vnd.bliz-mdx", ".m3")

# Python bugs
MimeType.registerExtension("application/x-font-ttf", ".ttf")
MimeType.registerExtension("audio/ogg", ".ogg")
"""

def getFirstTagData(element, tag):
	taglist = element.getElementsByTagName(tag)
	if taglist:
		child = taglist[0].firstChild
		if child:
			return str(child.data)
	return ""

def main():
	if len(sys.argv) < 2:
		print "No input file"
		exit(1)
	
	dom = parse(sys.argv[1])
	mimetypes = dom.getElementsByTagName("mime-type")
	
	out = {}
	for element in mimetypes:
		mime = str(element.getAttribute("type"))
		parent = getFirstTagData(element, "sub-class-of")
		comment = getFirstTagData(element, "comment")
		defaultIcon = getFirstTagData(element, "generic-icon")
		out[mime] = (parent, comment, defaultIcon)
	
	f = open("mpqt/_mime.py", "w")
	
	f.write(tpl % (out))


if __name__ == "__main__":
	main()
