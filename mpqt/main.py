# -*- coding: utf-8 -*-

import os.path
import sys
from optparse import OptionParser
from PySide.QtCore import *
from PySide.QtGui import *
from storm import MPQ

from . import utils
from .models import TreeModel, Directory
from .views import TreeView


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
		path = os.path.abspath(path)
		tabs = self.mainWindow.tabWidget
		for tab in range(tabs.count()):
			widget = tabs.widget(tab)
			tabpath = widget.model().file.filename
			if os.path.abspath(tabpath) == path:
				return tabs.setCurrentWidget(widget)
		
		try:
			self.mainWindow.addTab(MPQ(path))
			self.mainWindow.setWindowTitle("%s - MPQt" % (path))
		except Exception, e:
			self.mainWindow.statusBar().showMessage("Could not open %s" % (path))
			print "Could not open %r: %s" % (path, e)
	
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
		self.locationBar = QLineEdit()
		def setLocation():
			path = self.locationBar.text()
			if path.startswith("/"):
				path = path[1:]
			if path in self.currentModel().directories:
				self.currentModel().setPath(path)
		self.locationBar.returnPressed.connect(lambda: setLocation)
		toolbar.addWidget(self.locationBar)
	
	def actionActivateFile(self, index):
		model = self.currentModel()
		f = model.data(index)
		if isinstance(f, Directory):
			model.setPath(f.filename)
		elif f:
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
		
		def addFile(f):
			if isinstance(f, Directory):
				for subfile in self.currentModel().directories[f.filename.lower()]:
					addFile(subfile)
			else:
				extractList.add(f)
		
		for index in indexes:
			file = model.data(index)
			addFile(file)
		
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
		view = TreeView(self)
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


def main():
	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	app = MPQt(sys.argv)
	
	app.mainWindow.show()
	sys.exit(app.exec_())
