# -*- coding: utf-8 -*-

def hsize(i):
	"Human-readable file size"
	for x in ("%i B", "%3.1f KiB", "%3.1f MiB", "%3.1f GiB", "%3.1f TiB"):
		if i < 1024.0:
			return x % (i)
		i /= 1024.0

def splitpath(path):
	"Emulate windows splitpath"
	x = path.split("\\")
	if len(x) == 1:
		return "", x[0]
	return "\\".join(x[:-1]), x[-1]
