from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui

from maya.api import OpenMaya as om
from leg_component import LegComponent
from foot_component import FootComponent


def maya_main_window():
    """Return Maya Main Window Widget as Python object"""
    main_window_pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_pointer), QtWidgets.QWidget)


class LegRiggerUI(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(LegRiggerUI, self).__init__(parent)
        self.setWindowTitle("Leg Rigger")
        self.setMinimumWidth(200)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

        self.foot = FootComponent('l')

    def create_widgets(self):
        self.instruction = QtWidgets.QLabel('Select start and end of joint chain (e.g. hip and ankle) and fill in '
                                            'variables. When done press "Create"')
        self.line_group = QtWidgets.QLineEdit("LEG_RIG")
        self.line_side = QtWidgets.QLineEdit("l")
        self.checkbox1 = QtWidgets.QCheckBox()
        self.checkbox2 = QtWidgets.QCheckBox()
        self.guide_button = QtWidgets.QPushButton("Create Foot Guides")
        self.foot_instruction = QtWidgets.QLabel('To create the foot roll use a NURBS curve to create a profile of the'
                                                 'foot')
        self.create_button = QtWidgets.QPushButton("Create Leg Rig")
        self.cancel_button = QtWidgets.QPushButton("Cancel")

    def create_layouts(self):
        self.form_layout = QtWidgets.QFormLayout()
        self.instruction.setWordWrap(True)
        self.form_layout.addRow("Instruction:", self.instruction)
        self.form_layout.addRow("Rig Name:", self.line_group)
        self.form_layout.addRow("Side:", self.line_side)
        self.form_layout.addRow("IKFK Blend:", self.checkbox1)
        self.form_layout.addRow("Add Foot:", self.checkbox2)
        self.foot_instruction.setWordWrap(True)
        self.foot_instruction.setStyleSheet("color: gray")
        self.form_layout.addRow("Foot Instruction:", self.foot_instruction)
        self.form_layout.addRow("Foot:", self.guide_button)
        self.guide_button.setEnabled(False)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(self.form_layout)
        main_layout.addLayout(button_layout)

    def show_guide_button(self):
        foot = self.checkbox2.isChecked()
        if foot:
            self.guide_button.setEnabled(True)
            self.foot_instruction.setStyleSheet("color: white")
        else:
            self.guide_button.setEnabled(False)
            self.foot_instruction.setStyleSheet("color: grey")

    def create_connections(self):
        self.cancel_button.clicked.connect(self.close)
        self.create_button.clicked.connect(self.create_rig)
        self.guide_button.clicked.connect(self.create_foot_guides)
        self.checkbox2.toggled.connect(self.show_guide_button)

    def create_leg_rig(self):
        group_name = self.line_group.text()
        side = self.line_side.text()
        blend = self.checkbox1.isChecked()
        self.sel = om.MGlobal.getActiveSelectionList()
        self.leg = LegComponent(side)
        self.leg.construct_rig(group_name)
        self.leg.create_joints_parent(self.sel.getDependNode(0))
        fk_chain = self.leg.create_fk_chain(self.sel.getDependNode(0), self.sel.getDependNode(1))
        ik_chain = self.leg.create_ik_chain(self.sel.getDependNode(0), self.sel.getDependNode(1))
        fk_controls = self.leg.create_fk_controls()
        ik_controls = self.leg.create_ik_controls()
        ik_handle = self.leg.create_ik_handle(pole_vector=ik_controls[1].getDependNode(1))
        self.leg.create_fk_nodes_and_connections(fk_chain, fk_controls[1])
        self.leg.create_ik_nodes_and_connections(ik_chain, ik_controls[1].getDependNode(0), ik_handle)
        self.leg.create_ik_fk_switch(blend=blend)
        self.leg.attach_to_skin_chain()
        self.leg.create_and_connect_messages()
        self.leg.get_root()
        self.leg.get_groups()

    def create_foot_rig(self):
        self.foot.base_joint = self.sel.getDependNode(1)
        self.foot.side = self.line_side.text()
        self.foot.get_ik_fk_switch(self.foot.base_joint)
        self.foot.get_root()
        self.foot.get_groups()
        self.foot.get_foot_profile()
        foot_chain = self.foot.get_all_children(self.sel.getDependNode(1))
        self.foot.create_joints_parent(self.sel.getDependNode(1), string='foot_roll_')
        first_foot = foot_chain.getDependNode(0)
        last_foot = foot_chain.getDependNode(foot_chain.length() - 1)
        fk_chain = self.foot.create_fk_chain(first_foot, last_foot, string='foot_roll_')
        ik_chain = self.foot.create_ik_chain(first_foot, last_foot, string='foot_roll_')
        self.foot.create_ik_handle(ik_chain.getDependNode(0), ik_chain.getDependNode(1), limb='foot')
        self.foot.create_ik_handle(ik_chain.getDependNode(1), ik_chain.getDependNode(2), limb='toes')
        self.foot.create_foot_roll_control(last_foot, 'foot_roll')
        fk_controls = self.foot.create_fk_foot_controls(fk_chain)
        self.foot.create_fk_nodes_and_connections(joint_chain=fk_controls[1], joint_controls=fk_controls[0][1])
        foot_chain.remove(0)
        ik_chain.remove(0)
        self.foot.attach_to_skin_chain(ik_chain=ik_chain, fk_chain=fk_chain, skin_chain=foot_chain,
                                      ik_fk_switch=self.foot.ik_fk_switch)
        self.foot.create_foot_roll_setup()
        self.foot.fix_foot_setup()

    def create_foot_guides(self):
        self.foot = FootComponent(self.line_side.text())
        self.foot.create_foot_roll_guides()

    def create_rig(self):
        self.create_leg_rig()
        foot = self.checkbox2.isChecked()
        if foot:
            self.create_foot_rig()
