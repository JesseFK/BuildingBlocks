from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
from helper import Helper
from maya.api import OpenMaya as om
from leg_component import LegComponent
from foot_component import FootComponent


def maya_main_window():
    """Return Maya Main Window Widget as Python object"""
    main_window_pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_pointer), QtWidgets.QWidget)


class MasterUI(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(MasterUI, self).__init__(parent)
        self.setWindowTitle("Rigger")
        self.setMinimumWidth(200)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.set_widget_size()
        self.create_layouts()
        self.populate_combo_box()
        self.create_connections()

    def create_widgets(self):
        self.root_list = QtWidgets.QComboBox()
        self.name_box = QtWidgets.QLineEdit()
        self.groups_button = QtWidgets.QPushButton('Create Groups')
        self.leg_button = QtWidgets.QPushButton('Leg')
        self.foot_button = QtWidgets.QPushButton('Foot')
        self.arm_button = QtWidgets.QPushButton('Arm')
        self.hand_button = QtWidgets.QPushButton('Hand')
        self.spine_button = QtWidgets.QPushButton('Spine')
        self.chain_button = QtWidgets.QPushButton('Chain')

    def set_widget_size(self):
        self.leg_button.setMinimumHeight(40)
        self.foot_button.setMinimumHeight(40)
        self.arm_button.setMinimumHeight(40)
        self.hand_button.setMinimumHeight(40)
        self.spine_button.setMinimumHeight(40)
        self.chain_button.setMinimumHeight(40)

    def create_layouts(self):
        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.addRow("Root:", self.root_list)
        self.form_layout.addRow("Name:", self.name_box)
        self.form_layout.addRow(self.groups_button)

        self.button_layout = QtWidgets.QGridLayout()
        self.button_layout.addWidget(self.leg_button, 1, 1)
        self.button_layout.addWidget(self.arm_button, 1, 2)
        self.button_layout.addWidget(self.foot_button, 2, 1)
        self.button_layout.addWidget(self.hand_button, 2, 2)
        self.button_layout.addWidget(self.spine_button, 3, 1)
        self.button_layout.addWidget(self.chain_button, 3, 2)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(self.form_layout)
        main_layout.addLayout(self.button_layout)
        main_layout.addStretch()

    def populate_combo_box(self):
        helper = Helper()
        self.root_joints = helper.get_root_joints()
        joints_it = om.MItSelectionList(self.root_joints)
        while not joints_it.isDone():
            name = om.MFnDependencyNode(joints_it.getDependNode()).name()
            print(name)
            self.root_list.addItem(name)
            joints_it.next()

    def create_connections(self):
        pass