import time
import names
from helper import Helper
from leg_component import LegComponent
from maya import cmds
from maya import mel
from maya.api import OpenMaya as om


class FootComponent(LegComponent):
    # This class will be used to create the foot component
    # I've decided to split this up from the leg component since these are to me seen as seperate objects
    def __init__(self, side, base_joint=om.MObject()):
        super(FootComponent, self).__init__(side)
        self.base_joint = base_joint
        if not self.base_joint.isNull():
            self.get_ik_fk_switch(self.base_joint)
            self.get_root()
            self.get_groups()
        self.foot_profile = om.MObject()
        self.foot_chain = om.MSelectionList()

    def get_foot_profile(self, curve=om.MObject()):
        """ Get the foot profile curve
        :param curve: MObject containing foot profile
        :return: foot profile as MFnNurbsCurve
        """
        profile = om.MFnNurbsCurve(curve)
        self.foot_profile = profile
        return self.foot_profile

    def create_foot_roll_control(self, joint=om.MObject(), string=None, scale=2):
        """ Create foot roll control which is a stick like controller used for controlling the foot roll
        :param joint: Joint in the form of MObject
        :param string: string which is used for  name giving
        :param scale: scale multiplier of the control
        :return:
        """
        self.control_manager.manager.update_templates()
        remap_box = self.control_manager.create_control(joint, control='remap_box', name=string+'_box')
        remap_circle = self.control_manager.create_control(joint, control='remap_circle', name=string+'_circle')
        remap_ctrl = self.control_manager.create_control(joint, control='remap_ctrl', name=string)
        pin = self.control_manager.create_control(joint, control='pin_template', name=string+'_pin')
        remap_offset = self.control_manager.create_offset(remap_box)
        circle_offset = self.control_manager.create_offset(remap_ctrl)
        dag_mod = om.MDagModifier()
        circle_dag_node = om.MFnDagNode(remap_circle)
        circle_dag_path = circle_dag_node.getPath()
        circle_dag_path.extendToShape(0)
        dag_mod.reparentNode(circle_dag_path.node(), remap_box)
        pin_dag_node = om.MFnDagNode(pin)
        pin_dag_path = pin_dag_node.getPath()
        pin_dag_path.extendToShape(0)
        dag_mod.reparentNode(pin_dag_path.node(), remap_ctrl)
        dag_mod.reparentNode(circle_offset, remap_box)
        dag_mod.doIt()
        dag_mod.deleteNode(remap_circle)
        dag_mod.deleteNode(pin)
        ik_ctrl = None
        if not self.base_joint.isNull():
            self.get_ik_fk_switch(self.base_joint)
            ik_ctrl = self.get_ik_control()
            dag_mod.reparentNode(remap_offset, ik_ctrl)
        dag_mod.doIt()
        control_transform = self.control_manager.match_control(joint, remap_offset, rotation=False)
        joint_parent_path = om.MFnDagNode(om.MFnDagNode(joint).parent(0)).getPath()
        joint_parent_translate = om.MFnTransform(joint_parent_path).translation(4)
        joint_path = om.MFnDagNode(joint).getPath()
        joint_translate = om.MFnTransform(joint_path).translation(4)
        distance = om.MPoint(joint_translate).distanceTo(om.MPoint(joint_parent_translate))
        control_translation = control_transform.translation(4)
        new_translation = om.MVector(control_translation.x, control_translation.y, control_translation.z+(distance*1.2))
        control_transform.setTranslation(new_translation, 4)
        if not ik_ctrl is None:
            ik_ctrl_transform = om.MFnTransform(om.MFnDagNode(ik_ctrl).getPath())
            ik_ctrl_rot = ik_ctrl_transform.rotation(asQuaternion=True)
            temp_quaternion = om.MQuaternion(0.381, 0.314, 0.596, 0.633)
            control_transform.setRotation(temp_quaternion, 1)
        control_transform.setScale((scale, scale, scale))
        return (remap_box, remap_offset), (remap_ctrl, circle_offset)

    def get_ik_control(self):
        """ Method to get IK Control
        :return: IK Control as MObject
        """
        helper = Helper()
        plug = helper.get_plug(self.ik_fk_switch, 'l_ankle_ik_ctrl_match')
        return helper.get_plug_nodes(plug, 'l_ankle_ik_ctrl_match')[0]

    @staticmethod
    def create_foot_roll_setup():
        """ Due to time constraints this is the way I had to set up the foot roll which might be the dirtiest
        programming I have done in my life, obviously not reflective of the rest of the work, but I felt it important
        to include the foot roll in the rig.
        :return:
        """
        foot_profile = cmds.ls('l_foot_profileShape')[0]
        foot_roll_ctrl_circle = cmds.ls('foot_roll_circle_ctrlShape')[0]
        foot_roll_ctrl = cmds.ls('foot_roll_ctrl')[0]
        front_guide = cmds.ls('front_foot_roll_guide')[0]
        back_guide = cmds.ls('back_foot_roll_guide')[0]
        center_guide = cmds.ls('center_foot_roll_guide')[0]
        ik_ball = cmds.ls('l_foot_ball_foot_roll_ik')[0]
        ik_ankle = cmds.ls('l_ankle_foot_roll_ik')[0]

        fr_center = cmds.createNode('joint', name='foot_roll_center')
        fr_piv = cmds.createNode('joint', name='foot_roll_pivot')
        fr_recenter = cmds.createNode('joint', name='foot_roll_recenter')
        fr_back = cmds.createNode('joint', name='l_foot_back_foot_roll')
        fr_front = cmds.createNode('joint', name='l_foot_front_foot_roll')
        fr_ball = cmds.createNode('joint', name='l_foot_ball_foot_roll')
        fr_ankle = cmds.createNode('joint', name='l_foot_ankle_foot_roll')

        decompose1 = cmds.createNode('decomposeMatrix')
        near_point = cmds.createNode('nearestPointOnCurve')
        point_on_curve = cmds.createNode('pointOnCurveInfo')
        compose = cmds.createNode('composeMatrix')
        mult_mat = cmds.createNode('multMatrix')
        decompose2 = cmds.createNode('decomposeMatrix')
        remap1 = cmds.createNode('remapValue')
        remap2 = cmds.createNode('remapValue')
        add_rot = cmds.createNode('animBlendNodeAdditiveRotation')
        mult_div = cmds.createNode('multiplyDivide')

        remap3 = cmds.createNode('remapValue')
        remap4 = cmds.createNode('remapValue')

        cmds.connectAttr(foot_roll_ctrl + '.worldMatrix[0]', decompose1 + '.inputMatrix')
        cmds.connectAttr(decompose1 + '.outputTranslate', near_point + '.inPosition')
        cmds.connectAttr(foot_roll_ctrl_circle + '.worldSpace[0]', near_point + '.inputCurve')
        cmds.connectAttr(foot_profile + '.worldSpace[0]', point_on_curve + '.inputCurve')
        cmds.connectAttr(near_point + '.result.parameter', point_on_curve + '.parameter')
        cmds.connectAttr(point_on_curve + '.result.position', compose + '.inputTranslate')
        cmds.connectAttr(compose + '.outputMatrix', mult_mat + '.matrixIn[0]')
        cmds.connectAttr(fr_center + '.worldInverseMatrix[0]', mult_mat + '.matrixIn[1]')
        cmds.connectAttr(mult_mat + '.matrixSum', decompose2 + '.inputMatrix')
        cmds.connectAttr(foot_roll_ctrl + '.tx', remap1 + '.inputValue')
        cmds.connectAttr(foot_roll_ctrl + '.tz', remap2 + '.inputValue')
        cmds.setAttr(remap1 + '.inputMin', -1)
        cmds.setAttr(remap1 + '.inputMax', 1)
        cmds.setAttr(remap1 + '.outputMin', 0.167)
        cmds.setAttr(remap1 + '.outputMax', -0.167)
        cmds.setAttr(remap2 + '.inputMin', -1)
        cmds.setAttr(remap2 + '.inputMax', 2)
        cmds.setAttr(remap2 + '.outputMin', 0.167)
        cmds.setAttr(remap2 + '.outputMax', -0.167)
        cmds.setAttr(remap2 + '.value[2].value_Position', 0.333)
        cmds.setAttr(remap2 + '.value[2].value_FloatValue', 0.5)
        cmds.setAttr(remap2 + '.value[2].value_Interp', 1)
        cmds.connectAttr(remap1 + '.outValue', add_rot + '.weightB')
        cmds.connectAttr(remap2 + '.outValue', add_rot + '.weightA')
        cmds.setAttr(add_rot + '.inputAX', -360)
        cmds.setAttr(add_rot + '.inputBZ', 360)
        cmds.connectAttr(decompose2 + '.outputTranslate', fr_piv + '.t')
        cmds.connectAttr(add_rot + '.output', fr_piv + '.r')
        cmds.connectAttr(fr_piv + '.t', mult_div + '.input1')
        cmds.connectAttr(mult_div + '.output', fr_recenter + '.t')
        cmds.setAttr(mult_div + '.input2', -1, -1, -1, type='float3')

        cmds.connectAttr(foot_roll_ctrl + '.translateZ', remap3 + '.inputValue')
        cmds.connectAttr(foot_roll_ctrl + '.translateZ', remap4 + '.inputValue')
        cmds.setAttr(remap3 + '.inputMin', 0)
        cmds.setAttr(remap3 + '.inputMax', 2)
        cmds.setAttr(remap3 + '.outputMin', -60)
        cmds.setAttr(remap3 + '.outputMax', 0)
        cmds.setAttr(remap3 + '.value[0].value_Position', 0)
        cmds.setAttr(remap3 + '.value[0].value_FloatValue', 1)
        cmds.setAttr(remap3 + '.value[0].value_Interp', 1)
        cmds.setAttr(remap3 + '.value[2].value_Position', 0.5)
        cmds.setAttr(remap3 + '.value[2].value_FloatValue', 0.5)
        cmds.setAttr(remap3 + '.value[2].value_Interp', 1)
        cmds.setAttr(remap3 + '.value[1].value_Position', 1)
        cmds.setAttr(remap3 + '.value[1].value_FloatValue', 1)
        cmds.setAttr(remap3 + '.value[1].value_Interp', 1)
        cmds.setAttr(remap4 + '.inputMin', 0)
        cmds.setAttr(remap4 + '.inputMax', 2)
        cmds.setAttr(remap4 + '.outputMin', 0)
        cmds.setAttr(remap4 + '.outputMax', 60)
        cmds.setAttr(remap4 + '.value[2].value_Position', .5)
        cmds.setAttr(remap4 + '.value[2].value_FloatValue', 1)
        cmds.setAttr(remap4 + '.value[2].value_Interp', 1)
        cmds.setAttr(remap4 + '.value[1].value_Position', 1)
        cmds.setAttr(remap4 + '.value[1].value_FloatValue', 0)
        cmds.setAttr(remap4 + '.value[1].value_Interp', 1)
        cmds.connectAttr(remap3 + '.outValue', fr_front + '.rotateX')
        cmds.connectAttr(remap4 + '.outValue', fr_ball + '.rotateX')

        back_translate = cmds.xform(back_guide, q=True, ws=True, rp=True)
        front_translate = cmds.xform(front_guide, q=True, ws=True, rp=True)
        center_translate = cmds.xform(center_guide, q=True, ws=True, rp=True)
        ball_translate = cmds.xform(ik_ball, q=True, ws=True, rp=True)
        ankle_translate = cmds.xform(ik_ankle, q=True, ws=True, rp=True)
        cmds.setAttr(fr_back + '.t', *back_translate, type='float3')
        cmds.setAttr(fr_front + '.t', *front_translate, type='float3')
        cmds.setAttr(fr_center + '.t', *center_translate, type='float3')
        cmds.setAttr(fr_ball + '.t', *ball_translate, type='float3')
        cmds.setAttr(fr_ankle + '.t', *ankle_translate, type='float3')
        cmds.parent(fr_piv, fr_center)
        cmds.parent(fr_recenter, fr_piv)
        cmds.parent(fr_back, fr_recenter)
        cmds.parent(fr_front, fr_back)
        cmds.parent(fr_ball, fr_front)
        cmds.parent(fr_ankle, fr_ball)
        return fr_ankle, fr_ball, fr_front

    @staticmethod
    def fix_foot_setup():
        """Some fixes for the foot roll method above"""
        foot_profile = cmds.ls('l_foot_profile')[0]
        leg_ikHandle = cmds.ls('l_leg_ikHandle')[0]
        toes_ikHandle = cmds.ls('l_toes_ikHandle')[0]
        foot_ikHandle = cmds.ls('l_foot_ikHandle')[0]
        foot_ankle = cmds.ls('l_foot_ankle_foot_roll')[0]
        foot_ball = cmds.ls('l_foot_ball_foot_roll')[0]
        foot_toes = cmds.ls('l_foot_front_foot_roll')[0]
        foot_center = cmds.ls('foot_roll_center')[0]
        control_group = cmds.ls('CTRL')[0]
        foot_ik_ankle = cmds.ls('l_ankle_foot_roll_ik')[0]
        foot_joint_grp = cmds.ls('l_ankle_foot_roll_joints')[0]
        l_ankle_ik_mult_matrix = cmds.ls('l_ankle_ik_multMatrix')[0]

        foot_roll_grp = cmds.createNode('transform', n='foot_roll_grp')
        ik_ctrl = cmds.ls('l_ankle_ik_ctrl')[0]
        decompose = cmds.createNode('decomposeMatrix')
        cmds.connectAttr(ik_ctrl+'.worldMatrix', decompose+'.inputMatrix')
        cmds.connectAttr(decompose+'.outputTranslate', foot_roll_grp+'.t')
        cmds.connectAttr(decompose + '.outputRotate', foot_roll_grp + '.r')
        cmds.connectAttr(decompose + '.outputScale', foot_roll_grp + '.s')
        cmds.parent(foot_roll_grp, control_group)
        cmds.parent(foot_center, foot_roll_grp)
        cmds.parent(foot_profile, foot_roll_grp)
        cmds.hide(foot_profile)

        mel.eval('CBdeleteConnection {0}'.format(leg_ikHandle+'.tx'))
        mel.eval('CBdeleteConnection {0}'.format(leg_ikHandle+'.ty'))
        mel.eval('CBdeleteConnection {0}'.format(leg_ikHandle+'.tz'))
        cmds.parent(leg_ikHandle, foot_ankle)
        cmds.parent(foot_ikHandle, foot_ball)
        cmds.parent(toes_ikHandle, foot_toes)

        mult_m = cmds.createNode('multMatrix')
        decompose2 = cmds.createNode('decomposeMatrix')
        cmds.connectAttr(foot_ankle+'.worldMatrix[0]', mult_m+'.matrixIn[0]')
        cmds.connectAttr(foot_joint_grp + '.worldInverseMatrix[0]', mult_m + '.matrixIn[1]')
        cmds.connectAttr(mult_m+'.matrixSum', decompose2+'.inputMatrix')
        cmds.connectAttr(decompose2+'.outputTranslate', foot_ik_ankle+'.t')
        cmds.connectAttr(foot_ik_ankle+'.worldMatrix[0]', l_ankle_ik_mult_matrix+'.matrixIn[0]', f=True)


    @staticmethod
    def create_foot_roll_guides():
        """ Method that creates guides for the foot roll setup
        :return: guides as MSelectionList
        """
        dag_mod = om.MDagModifier()
        front = dag_mod.createNode('locator')
        back = dag_mod.createNode('locator')
        center = dag_mod.createNode('locator')
        guide_list = om.MSelectionList()
        guide_list.add(front)
        guide_list.add(back)
        guide_list.add(center)
        dag_mod.renameNode(front, 'front_foot_roll_guide')
        dag_mod.renameNode(back, 'back_foot_roll_guide')
        dag_mod.renameNode(center, 'center_foot_roll_guide')
        dag_mod.doIt()
        return guide_list

    def create_fk_foot_controls(self, chain=om.MSelectionList()):
        """ Method to create FK Controls from the given chain
        :param chain: MSelectionList containing FK Chain
        :return: controls and chain as MSelectionLists
        """
        helper = Helper()
        chain.remove(0)
        controls = self.create_fk_controls(chain)
        parent = om.MFnDagNode(controls[0].getDependNode(0)).parent(0)
        plug = helper.get_plug(self.ik_fk_switch, 'l_ankle_fk_ctrl')
        ankle_fk_ctrl = helper.get_plug_nodes(plug, 'l_ankle_fk_ctrl')[0]
        dg_mod = om.MDGModifier()
        decompose = dg_mod.createNode('decomposeMatrix')
        ankle_world = helper.get_plug(ankle_fk_ctrl, 'worldMatrix')
        parent_t = helper.get_plug(parent, 'translate')
        parent_r = helper.get_plug(parent, 'rotate')
        parent_s = helper.get_plug(parent, 'scale')
        decompose_in = helper.get_plug(decompose, 'inputMatrix')
        decompose_out_t = helper.get_plug(decompose, 'outputTranslate')
        decompose_out_r = helper.get_plug(decompose, 'outputRotate')
        decompose_out_s = helper.get_plug(decompose, 'outputScale')
        dg_mod.connect(ankle_world.elementByLogicalIndex(0), decompose_in)
        dg_mod.connect(decompose_out_t, parent_t)
        dg_mod.connect(decompose_out_r, parent_r)
        dg_mod.connect(decompose_out_s, parent_s)
        dg_mod.doIt()
        return controls, chain
