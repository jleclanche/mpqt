#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from xml.dom.minidom import parse

tpl = """# -*- coding: utf-8 -*-
import os.path
from mimetypes import types_map

comments_map = %r

DEFAULT_MIME_TYPE = "application/octet-stream"

class MimeType(object):
	
	def __init__(self, mime):
		if mime not in comments_map:
			mime = DEFAULT_MIME_TYPE
		self.__mimeType = mime
	
	@classmethod
	def fromName(cls, f):
		_, ext = os.path.splitext(f)
		if ext not in types_map: # Always try a case-sensitive match first
			ext = ext.lower()
		if ext in types_map:
			mime = types_map[ext]
		else:
			mime = DEFAULT_MIME_TYPE
		return cls(mime)
	
	def comment(self):
		return comments_map[self.mimeType()]
	
	def mimeType(self):
		return self.__mimeType
"""

def main():
	if len(sys.argv) < 2:
		print "No input file"
		exit(1)
	
	dom = parse(sys.argv[1])
	mimetypes = dom.getElementsByTagName("mime-type")
	
	out = {}
	for element in mimetypes:
		mime = element.getAttribute("type")
		comments = element.getElementsByTagName("comment")
		comment = comments[0].firstChild.data
		out[mime] = comment
	
	f = open("_mime.py", "w")
	
	f.write(tpl % (out))


if __name__ == "__main__":
	main()
