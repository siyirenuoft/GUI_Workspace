# Form implementation generated from reading ui file 'layout.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1060, 742)
        MainWindow.setStyleSheet("background-color: rgb(245, 250, 254);")
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.splitter_4 = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter_4.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter_4.setObjectName("splitter_4")
        self.splitter_2 = QtWidgets.QSplitter(parent=self.splitter_4)
        self.splitter_2.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.widget = QtWidgets.QWidget(parent=self.splitter_2)
        self.widget.setObjectName("widget")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_8.setObjectName("gridLayout_8")
        spacerItem = QtWidgets.QSpacerItem(978, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_8.addItem(spacerItem, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(0, 368, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout_8.addItem(spacerItem1, 0, 1, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(parent=self.widget)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.treeWidget = QtWidgets.QTreeWidget(parent=self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setMaximumSize(QtCore.QSize(121, 16777215))
        self.treeWidget.setStyleSheet("background-color: rgb(255, 0, 255);")
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.gridLayout_7.addWidget(self.treeWidget, 0, 0, 1, 1)
        self.splitter_6 = QtWidgets.QSplitter(parent=self.groupBox)
        self.splitter_6.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter_6.setObjectName("splitter_6")
        self.widget1 = QtWidgets.QWidget(parent=self.splitter_6)
        self.widget1.setObjectName("widget1")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.widget1)
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.splitter_5 = QtWidgets.QSplitter(parent=self.widget1)
        self.splitter_5.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter_5.setObjectName("splitter_5")
        self.splitter = QtWidgets.QSplitter(parent=self.splitter_5)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")
        self.pushButton = QtWidgets.QPushButton(parent=self.splitter)
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.splitter)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout_6.addWidget(self.splitter_5, 0, 0, 1, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.widget2 = QtWidgets.QWidget(parent=self.widget1)
        self.widget2.setStyleSheet("background-color: rgb(255, 0, 127);")
        self.widget2.setObjectName("widget2")
        self.gridLayout.addWidget(self.widget2, 0, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(13, 58, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(spacerItem2, 0, 1, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(648, 17, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout.addItem(spacerItem3, 1, 0, 1, 1)
        self.gridLayout_6.addLayout(self.gridLayout, 0, 1, 1, 1)
        self.widget3 = QtWidgets.QWidget(parent=self.splitter_6)
        self.widget3.setObjectName("widget3")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.widget3)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        spacerItem4 = QtWidgets.QSpacerItem(0, 224, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout_5.addItem(spacerItem4, 0, 1, 1, 1)
        spacerItem5 = QtWidgets.QSpacerItem(808, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_5.addItem(spacerItem5, 1, 0, 1, 1)
        self.widget_2 = QtWidgets.QWidget(parent=self.widget3)
        self.widget_2.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.widget_2.setObjectName("widget_2")
        self.gridLayout_5.addWidget(self.widget_2, 0, 0, 1, 1)
        self.gridLayout_7.addWidget(self.splitter_6, 0, 1, 1, 1)
        self.gridLayout_8.addWidget(self.groupBox, 0, 0, 1, 1)
        self.splitter_3 = QtWidgets.QSplitter(parent=self.splitter_4)
        self.splitter_3.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter_3.setObjectName("splitter_3")
        self.widget4 = QtWidgets.QWidget(parent=self.splitter_3)
        self.widget4.setObjectName("widget4")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.widget4)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        spacerItem6 = QtWidgets.QSpacerItem(0, 188, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout_3.addItem(spacerItem6, 0, 1, 1, 1)
        spacerItem7 = QtWidgets.QSpacerItem(822, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_3.addItem(spacerItem7, 1, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(parent=self.widget4)
        self.groupBox_2.setStyleSheet("")
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        spacerItem8 = QtWidgets.QSpacerItem(0, 148, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout_2.addItem(spacerItem8, 0, 1, 1, 1)
        spacerItem9 = QtWidgets.QSpacerItem(758, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_2.addItem(spacerItem9, 1, 0, 1, 1)
        self.widget_3 = QtWidgets.QWidget(parent=self.groupBox_2)
        self.widget_3.setStyleSheet("background-color: rgb(170, 170, 255);")
        self.widget_3.setObjectName("widget_3")
        self.gridLayout_2.addWidget(self.widget_3, 0, 0, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_2, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)
        self.gridLayout_9.addWidget(self.splitter_4, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1060, 22))
        self.menubar.setObjectName("menubar")
        self.menuMenu = QtWidgets.QMenu(parent=self.menubar)
        self.menuMenu.setObjectName("menuMenu")
        self.menuCanvas = QtWidgets.QMenu(parent=self.menubar)
        self.menuCanvas.setObjectName("menuCanvas")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionStart_New_Design = QtGui.QAction(parent=MainWindow)
        self.actionStart_New_Design.setObjectName("actionStart_New_Design")
        self.actionSave_New_Design = QtGui.QAction(parent=MainWindow)
        self.actionSave_New_Design.setObjectName("actionSave_New_Design")
        self.actionImport_Waveform = QtGui.QAction(parent=MainWindow)
        self.actionImport_Waveform.setObjectName("actionImport_Waveform")
        self.actionCreate_New_Chain = QtGui.QAction(parent=MainWindow)
        self.actionCreate_New_Chain.setObjectName("actionCreate_New_Chain")
        self.actionAdd_One_Unit = QtGui.QAction(parent=MainWindow)
        self.actionAdd_One_Unit.setObjectName("actionAdd_One_Unit")
        self.menuMenu.addAction(self.actionStart_New_Design)
        self.menuMenu.addAction(self.actionSave_New_Design)
        self.menuMenu.addAction(self.actionImport_Waveform)
        self.menuCanvas.addAction(self.actionCreate_New_Chain)
        self.menuCanvas.addAction(self.actionAdd_One_Unit)
        self.menubar.addAction(self.menuMenu.menuAction())
        self.menubar.addAction(self.menuCanvas.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox.setTitle(_translate("MainWindow", "Canvas"))
        self.pushButton.setText(_translate("MainWindow", "Clear"))
        self.pushButton_2.setText(_translate("MainWindow", "Save Signal"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Timeline"))
        self.menuMenu.setTitle(_translate("MainWindow", "File"))
        self.menuCanvas.setTitle(_translate("MainWindow", "Canvas"))
        self.actionStart_New_Design.setText(_translate("MainWindow", "Start New Design"))
        self.actionSave_New_Design.setText(_translate("MainWindow", "Save New Design"))
        self.actionImport_Waveform.setText(_translate("MainWindow", "Import Waveform"))
        self.actionCreate_New_Chain.setText(_translate("MainWindow", "Create New Chain"))
        self.actionAdd_One_Unit.setText(_translate("MainWindow", "Add One Unit"))
