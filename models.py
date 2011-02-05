# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import QIcon
from _mime import MimeType
import utils

class Directory(str):
	"""
	Emulates a directory within a MPQ
	MPQs don't have a concept of directories so we create them ourselves.
	A dir is just a string (the path), but we do need to store the full path.
	"""
	def __new__(cls, path):
		_, name = utils.splitpath(path)
		instance = str.__new__(cls, name)
		instance.filename = path
		instance.plainpath = name
		instance.mimetype = MimeType("inode/directory")
		return instance

COLUMN_NAME = 0
COLUMN_SIZE = 1
COLUMN_TYPE = 2

class BaseModel(object):
	_COLS = ("Name", "Size", "Type")
	
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
			path, _ = utils.splitpath(f.filename) # Emulate unix os.path.split
			path = path.lower()
			def addpath(path):
				if path not in self.directories:
					self.directories[path] = []
					if path:
						parent, dirname = utils.splitpath(path)
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
		self.path = path
		path = path.replace("\\", "/")
		#qApp.mainWindow.locationBar.setText("/%s" % (path))
		#qApp.mainWindow.statusBar().showMessage("%s:/%s" % (os.path.basename(self.file.filename), path))


class ListModel(QAbstractListModel, BaseModel):
	def __init__(self, parent=None):
		super(ListModel, self).__init__(parent)
		self.rows = []
	
	def data(self, index, role=-1):
		if index.row() > len(self.rows):
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


class TreeModel(QAbstractItemModel, BaseModel):
	def __init__(self, parent=None):
		super(TreeModel, self).__init__(parent)
		self.rows = []
	
	def columnCount(self, parent):
		return len(self._COLS)
	
	def data(self, index, role=-1):
		if index.row() >= len(self.rows):
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
				return utils.hsize(file.filesize)
			
			if column == COLUMN_TYPE:
				if not hasattr(file, "mimetype"):
					file.mimetype = MimeType.fromName(file.plainpath)
				return file.mimetype.comment()
		
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
			self.rows.sort(key=lambda x: x.plainpath)
		
		elif column == COLUMN_SIZE:
			self.rows.sort(key=sortBySize)
		
		elif column == COLUMN_TYPE:
			self.rows.sort(key=lambda x: x.mimetype.comment())
		
		if order == Qt.AscendingOrder:
			self.rows.reverse()
		
		self.emit(SIGNAL("layoutChanged()"))
