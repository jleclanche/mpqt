#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from optparse import OptionParser
from PySide.QtCore import *
from PySide.QtGui import *
from storm import MPQ


class MPQt(QApplication):
	def __init__(self, argv):
		QApplication.__init__(self, argv)
		self.mainWindow = MainWindow()
		self.mainWindow.setWindowTitle("MPQt")
		self.mainWindow.resize(1024, 768)
		
		arguments = OptionParser()
		
		_, files = arguments.parse_args(argv[1:])
		
		self.mainWindow.statusBar().showMessage("Ready")
		
		for name in files:
			self.open(name)
	
	def open(self, name):
		self.mpq = MPQ(name)
		self.mainWindow.model.setFile(self.mpq)
		self.mainWindow.setWindowTitle("%s - MPQt" % (name))

class MainWindow(QMainWindow):
	def __init__(self, *args):
		QMainWindow.__init__(self, *args)
		
		self.__addMenus()
		self.__addToolbar()
		
		self.model = MPQArchiveListModel()
		
		view = QListView()
		view.setFlow(QListView.TopToBottom)
		view.setLayoutMode(QListView.SinglePass)
		view.setResizeMode(QListView.Adjust)
		view.setSpacing(1)
		view.setViewMode(QListView.ListMode)
		view.setWrapping(True)
		
		def openFile(index):
			f = self.model.data(index)
			if isinstance(f, Directory):
				self.model.setPath(f.filename)
			else:
				print "Opening file %s not implemented" % (f.filename)
		view.activated.connect(openFile)
		
		#view = QTreeView()
		
		view.setModel(self.model)
		self.setCentralWidget(view)
	
	def __addMenus(self):
		fileMenu = self.menuBar().addMenu("&File")
		fileMenu.addAction(QIcon.fromTheme("document-new"), "&New", self.actionNew, "Ctrl+N")
		fileMenu.addAction(QIcon.fromTheme("document-open"), "&Open...", self.actionOpen, "Ctrl+O")
		recentMenuItem = fileMenu.addAction(QIcon.fromTheme("document-open-recent"), "Open &Recent")
		recentMenuItem.setDisabled(True)
		fileMenu.addSeparator()
		fileMenu.addAction(QIcon.fromTheme("application-exit"), "&Quit", self, SLOT("close()"), "Ctrl+Q")
		
		fileMenu = self.menuBar().addMenu("&Help")
		fileMenu.addAction(QIcon.fromTheme("help-about"), "About", lambda: None)
	
	def __addToolbar(self):
		toolbar = self.addToolBar("Toolbar")
		toolbar.addAction(QIcon.fromTheme("document-new"), "New").triggered.connect(self.actionNew)
		toolbar.addAction(QIcon.fromTheme("document-open"), "Open").triggered.connect(self.actionOpen)
		fileMask = QLineEdit()
		fileMask.setPlaceholderText("File mask")
		toolbar.addWidget(fileMask)
	
	def actionNew(self):
		print "actionNew()"
	
	def actionOpen(self):
		filename, filters = QFileDialog.getOpenFileName(self, "Open file", "", "Blizzard MPQ archives (*.mpq);;All files (*.*)")
		if filename:
			qApp.open(filename)


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

class Directory(str):
	"""
	Emulates a directory within a MPQ
	MPQs don't have a concept of directories so we create them ourselves.
	A dir is just a string (the path), but we do need to store the full path.
	"""
	def __new__(cls, path):
		_, name = splitpath(path)
		instance = str.__new__(cls, name)
		instance.filename = path
		instance.plainpath = name
		return instance

class MPQArchiveBaseModel(object):
	_COLS = ("Name", "Size")
	
	def __init__(self):
		self.rows = []
	
	def setFile(self, file):
		self.rows = []
		self.files = []
		self.directories = {} # emulate a directory structure
		for f in file.list():
			self.files.append(f)
			path, _ = splitpath(f.filename) # Emulate unix os.path.split
			def addpath(path):
				if path not in self.directories:
					self.directories[path] = []
					if path:
						parent, dirname = splitpath(path)
						if parent not in self.directories:
							addpath(parent)
						self.directories[parent].append(Directory(path))
			
			addpath(path)
			self.directories[path].append(f)
		self.setPath("")
	
	def setPath(self, path):
		self.emit(SIGNAL("layoutAboutToBeChanged()"))
		self.rows = self.directories[path]
		self.emit(SIGNAL("layoutChanged()"))
		_, mpq = os.path.split(qApp.mpq.filename)
		qApp.mainWindow.statusBar().showMessage("%s:/%s" % (mpq, path.replace("\\", "/")))


class MPQArchiveListModel(QAbstractListModel, MPQArchiveBaseModel):
	def __init__(self, *args):
		QAbstractListModel.__init__(self, *args)
		self.rows = []
	
	def data(self, index, role=-1):
		if index.row() >= len(self.rows):
			return
		file = self.rows[index.row()]
		
		if role == -1:
			return self.rows[index.row()]
		
		if role == Qt.DisplayRole:
			return self.rows[index.row()].plainpath
		
		if role == Qt.DecorationRole:
			ext = file.filename.lower()
			if isinstance(file, Directory):
				return QIcon.fromTheme("folder")
			
			if ext.endswith(".blp"):
				return QIcon.fromTheme("image-x-generic")
			
			if ext.endswith(".exe"):
				return QIcon.fromTheme("application-x-executable")
			
			if ext.endswith(".mp3") or ext.endswith(".ogg") or ext.endswith(".wav"):
				return QIcon.fromTheme("audio-x-generic")
			
			if ext.endswith(".ttf"):
				return QIcon.fromTheme("font-x-generic")
			
			return QIcon.fromTheme("text-x-generic")
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self._COLS[0]
		
		return QAbstractItemModel.headerData(self, section, orientation, role)
	
	def rowCount(self, parent):
		return len(self.rows)


COLUMN_NAME = 0
COLUMN_SIZE = 1

class MPQArchiveTreeModel(QAbstractItemModel, MPQArchiveBaseModel):
	def __init__(self, *args):
		QAbstractItemModel.__init__(self, *args)
		self.rows = []
	
	def columnCount(self, parent):
		return len(self._COLS)
	
	def data(self, index, role):
		if not index.isValid() or role != Qt.DisplayRole:
			return
		
		file = self.rows[index.row()]
		
		column = index.column()
		if column == COLUMN_NAME:
			if isinstance(file, Directory):
				return file
			return file.plainpath
		
		if column == COLUMN_SIZE:
			if isinstance(file, Directory):
				items = len(self.directories[file])
				if items == 1:
					return "1 item"
				return "%i items" % (items)
			return hsize(file.filesize)
		
		return -1
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self._COLS[section]
		return QAbstractItemModel.headerData(self, section, orientation, role)
	
	def index(self, row, column, parent):
		if not self.hasIndex(row, column, parent):
			return QModelIndex()
		
		if not parent.isValid():
			return self.createIndex(row, column)
		
		return QModelIndex()
	
	def parent(self, index):
		if not index.isValid():
			return QModelIndex()
		
		return QModelIndex()
	
	def rowCount(self, parent):
		return len(self.rows)



def main():
	import signal
	import sys
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	app = MPQt(sys.argv)
	
	app.mainWindow.show()
	sys.exit(app.exec_())

if __name__ == "__main__":
	main()
