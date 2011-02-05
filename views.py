# -*- coding: utf-8 -*-

from PySide.QtCore import Qt
from PySide.QtGui import *


class ListView(QListView):
	def __init__(self, parent=None):
		super(ListView, self).__init__(parent)
		self.setFlow(QListView.TopToBottom)
		self.setLayoutMode(QListView.SinglePass)
		self.setResizeMode(QListView.Adjust)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setSelectionRectVisible(True)
		self.setSpacing(1)
		self.setViewMode(QListView.ListMode)
		self.setWrapping(True)
		self.activated.connect(parent.actionActivateFile)
		
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(parent.createContextMenu)


class TreeView(QTreeView):
	def __init__(self, parent=None):
		super(TreeView, self).__init__(parent)
		self.setRootIsDecorated(False)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		#self.setSelectionRectVisible(True)
		self.setSortingEnabled(True)
		self.activated.connect(parent.actionActivateFile)
		self.header().setResizeMode(QHeaderView.Stretch)
		
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(parent.createContextMenu)