#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import sys
from optparse import OptionParser
from PySide.QtCore import *
from PySide.QtGui import *
from storm import MPQ
from time import sleep


# Helpers
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
	
	def open(self, path):
		self.mainWindow.addTab(MPQ(path))
		self.mainWindow.setWindowTitle("%s - MPQt" % (path))
	
	def extract(self, file, target):
		self.mainWindow.currentModel().file.extract(file, target)


class MainWindow(QMainWindow):
	def __init__(self, *args):
		QMainWindow.__init__(self, *args)
		
		self.__addMenus()
		self.__addToolbar()
		
		self.tabWidget = QTabWidget()
		self.tabWidget.setDocumentMode(True)
		self.tabWidget.setMovable(True)
		self.tabWidget.setTabsClosable(True)
		self.tabWidget.tabCloseRequested.connect(self.actionCloseTab)
		self.setCentralWidget(self.tabWidget)
	
	def __addMenus(self):
		def closeOrExit():
			index = self.tabWidget.currentIndex()
			if index == -1:
				self.close()
			else:
				self.actionCloseTab(index)
		
		fileMenu = self.menuBar().addMenu("&File")
		fileMenu.addAction(QIcon.fromTheme("document-new"), "&New", self.actionNew, "Ctrl+N")
		fileMenu.addAction(QIcon.fromTheme("document-open"), "&Open...", self.actionOpen, "Ctrl+O")
		fileMenu.addAction(QIcon.fromTheme("document-open-recent"), "Open &Recent").setDisabled(True)
		fileMenu.addSeparator()
		fileMenu.addAction(QIcon.fromTheme("window-close"), "&Close", closeOrExit, "Ctrl+W")
		fileMenu.addSeparator()
		fileMenu.addAction(QIcon.fromTheme("application-exit"), "&Quit", self.close, "Ctrl+Q")
		
		goMenu = self.menuBar().addMenu("&Go")
		goMenu.addAction(QIcon.fromTheme("go-up"), "&Up", self.actionGoUp, "Alt+Up")
		goMenu.addAction(QIcon.fromTheme("go-previous"), "&Back", self.actionGoUp, "Alt+Left")
		goMenu.addAction(QIcon.fromTheme("go-next"), "&Forward", self.actionGoUp, "Alt+Right")
		goMenu.addAction(QIcon.fromTheme("go-home"), "&Root", lambda: self.currentModel().setPath(""), "Alt+Home")
		
		helpMenu = self.menuBar().addMenu("&Help")
		helpMenu.addAction(QIcon.fromTheme("help-about"), "About")
	
	def __addToolbar(self):
		toolbar = self.addToolBar("Toolbar")
		toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
		toolbar.addAction(QIcon.fromTheme("document-new"), "New").triggered.connect(self.actionNew)
		toolbar.addAction(QIcon.fromTheme("document-open"), "Open").triggered.connect(self.actionOpen)
		toolbar.addSeparator()
		toolbar.addAction(QIcon.fromTheme("go-previous"), "Back")
		toolbar.addAction(QIcon.fromTheme("go-next"), "Forward")
		toolbar.addAction(QIcon.fromTheme("go-up"), "Up").triggered.connect(self.actionGoUp)
		toolbar.addSeparator()
		fileMask = QLineEdit()
		fileMask.setPlaceholderText("File mask")
		fileMask.returnPressed.connect(lambda: self.currentModel().setPath(""))
		toolbar.addWidget(fileMask)
	
	def actionActivateFile(self, index):
		model = self.currentModel()
		f = model.data(index)
		if isinstance(f, Directory):
			model.setPath(f.filename)
		else:
			print "Opening file %s not implemented" % (f.filename)
	
	def actionCloseTab(self, index):
		widget = self.tabWidget.widget(index)
		# BUG crashes in FreeMPQArchive()
		#widget.model().file.close()
		#del widget.model().file
		del widget
		self.tabWidget.removeTab(index)
	
	def actionExtract(self):
		indexes = self.tabWidget.currentWidget().selectedIndexes()
		model = self.currentModel()
		extractList = set()
		for index in indexes:
			file = model.data(index)
			if isinstance(file, Directory):
				for subfile in self.currentModel().file.list("%s\\*" % (file)):
					# Recursively extract files within a directory
					extractList.add(subfile)
			else:
				extractList.add(file)
		
		total = len(extractList)
		i = 0
		lenOut = 0
		for file in extractList:
			i += 1
			pc = (i / total) * 100
			print "\r" + " " * lenOut,
			out = "Extracting %i/%i (%i%%)... %s" % (i, total, pc, file)
			lenOut = len(out)
			print "\r" + out,
			self.statusBar().showMessage(out)
			sys.stdout.flush()
			qApp.extract(file, os.path.basename(model.file.filename))
		
		if total:
			out = "Extracted %i files" % (total)
			print "\n" + out
			self.statusBar().showMessage(out)
	
	def actionGoUp(self):
		model = self.currentModel()
		path = model.path.split("\\")
		model.setPath("\\".join(path[:-1]))
	
	def actionNew(self):
		print "actionNew()"
	
	def actionOpen(self):
		filename, filters = QFileDialog.getOpenFileName(self, "Open file", "", "Blizzard MPQ archives (*.mpq);;All files (*.*)")
		if filename:
			qApp.open(str(filename))
	
	def addTab(self, file):
		view = TreeView()
		model = TreeModel()
		model.setFile(file)
		view.setModel(model)
		view._m_model = model # BUG
		self.tabWidget.addTab(view, QIcon.fromTheme("package-x-generic"), os.path.basename(file.filename))
	
	def createContextMenu(self, pos):
		contextMenu = QMenu()
		indexes = self.tabWidget.currentWidget().selectedIndexes()
		if not indexes:
			contextMenu.addAction("<No file selected>").setDisabled(True)
		else:
			contextMenu.addAction("Extract", self.actionExtract, "Ctrl+E")
			contextMenu.addAction(QIcon.fromTheme("edit-delete"), "Delete", lambda: None, "Del").setDisabled(True)
			contextMenu.addSeparator()
			contextMenu.addAction(QIcon.fromTheme("document-properties"), "Properties", lambda: None, "Alt+Return")
		contextMenu.exec_(self.tabWidget.currentWidget().mapToGlobal(pos))
	
	def currentModel(self):
		view = self.tabWidget.currentWidget()
		return view._m_model # BUG


class ListView(QListView):
	def __init__(self, *args):
		QListView.__init__(self, *args)
		self.setFlow(QListView.TopToBottom)
		self.setLayoutMode(QListView.SinglePass)
		self.setResizeMode(QListView.Adjust)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setSelectionRectVisible(True)
		self.setSpacing(1)
		self.setViewMode(QListView.ListMode)
		self.setWrapping(True)
		self.activated.connect(qApp.mainWindow.actionActivateFile)
		
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(qApp.mainWindow.createContextMenu)


class TreeView(QTreeView):
	def __init__(self, *args):
		QTreeView.__init__(self, *args)
		self.setRootIsDecorated(False)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		#self.setSelectionRectVisible(True)
		self.setSortingEnabled(True)
		self.activated.connect(qApp.mainWindow.actionActivateFile)
		self.header().setResizeMode(QHeaderView.Stretch)
		
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(qApp.mainWindow.createContextMenu)


class BaseModel(object):
	_COLS = ("Name", "Size")
	
	def iconForExtension(self, ext):
		if ext.endswith(".blp"):
			return QIcon.fromTheme("image-x-generic")
		
		if ext.endswith(".dbc") or ext.endswith(".db2"):
			return QIcon.fromTheme("x-office-spreadsheet")
		
		if ext.endswith(".exe"):
			return QIcon.fromTheme("application-x-executable")
		
		if ext.endswith(".mp3") or ext.endswith(".ogg") or ext.endswith(".wav"):
			return QIcon.fromTheme("audio-x-generic")
		
		if ext.endswith(".ttf"):
			return QIcon.fromTheme("font-x-generic")
		
		return QIcon.fromTheme("text-x-generic")
	
	def setFile(self, file):
		self.file = file
		self.rows = []
		self.files = []
		self.directories = {} # emulate a directory structure
		for f in file.list():
			self.files.append(f)
			path, _ = splitpath(f.filename) # Emulate unix os.path.split
			path = path.lower()
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
		qApp.mainWindow.statusBar().showMessage("%s:/%s" % (os.path.basename(self.file.filename), path.replace("\\", "/")))


class ListModel(QAbstractListModel, BaseModel):
	def __init__(self, *args):
		super(ListModel, self).__init__(*args)
		self.rows = []
	
	def data(self, index, role=-1):
		if not index.isValid():
			return
		
		file = self.rows[index.row()]
		
		if role == -1:
			return file
		
		if role == Qt.DisplayRole:
			return file.plainpath
		
		if role == Qt.DecorationRole:
			ext = file.filename.lower()
			if isinstance(file, Directory):
				return QIcon.fromTheme("folder")
			
			return self.iconForExtension(ext)
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self._COLS[0]
		
		return QAbstractItemModel.headerData(self, section, orientation, role)
	
	def rowCount(self, parent=QModelIndex()):
		return len(self.rows)


COLUMN_NAME = 0
COLUMN_SIZE = 1

class TreeModel(QAbstractItemModel, BaseModel):
	def __init__(self, *args):
		QAbstractItemModel.__init__(self, *args)
		self.rows = []
	
	def columnCount(self, parent):
		return len(self._COLS)
	
	def data(self, index, role=-1):
		if not index.isValid():
			return
		
		file = self.rows[index.row()]
		column = index.column()
		
		if role == -1:
			return file
		
		if role == Qt.DisplayRole:
			if column == COLUMN_NAME:
				if isinstance(file, Directory):
					return file
				return file.plainpath
			
			if column == COLUMN_SIZE:
				if isinstance(file, Directory):
					items = len(self.directories[file.filename])
					if items == 1:
						return "1 item"
					return "%i items" % (items)
				return hsize(file.filesize)
		
		if role == Qt.DecorationRole:
			if column == COLUMN_NAME:
				ext = file.filename.lower()
				if isinstance(file, Directory):
					return QIcon.fromTheme("folder")
				
				return self.iconForExtension(ext)
	
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
	
	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0
		return len(self.rows)
	
	def sort(self, column, order=Qt.AscendingOrder):
		self.emit(SIGNAL("layoutAboutToBeChanged()"))
		
		def sortBySize(item):
			if isinstance(item, Directory):
				return len(self.directories[item.filename])
			return -item.filesize
		
		if column == COLUMN_NAME:
			self.rows.sort()
		
		elif column == COLUMN_SIZE:
			self.rows.sort(key=sortBySize)
		
		if order == Qt.AscendingOrder:
			self.rows.reverse()
		
		self.emit(SIGNAL("layoutChanged()"))


def main():
	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	app = MPQt(sys.argv)
	
	app.mainWindow.show()
	sys.exit(app.exec_())

if __name__ == "__main__":
	main()
