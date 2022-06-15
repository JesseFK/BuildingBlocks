import names
from master_component import MasterComponent
from helper import Helper
from maya import cmds
from maya.api import OpenMaya as om
from controller_manager import ControllerManager


class LegComponent(MasterComponent):
    """
    This is the leg component class which derives from the MasterComponent class.
    :param side: The only argument that the __init__ method requires is a side variable which is used in various methods
    Most use cases of the number 4 will be referring to MSpace.kWorld = 4
    """
    def __init__(self, side):
        super(LegComponent, self).__init__()
        self.skinned_chain = om.MSelectionList()
        self.ik_chain = om.MSelectionList()
        self.ik_root = om.MObject()
        self.fk_chain = om.MSelectionList()
        self.ik_handle = om.MObject()
        self.control_manager = ControllerManager()
        self.fk_offsets = om.MSelectionList()
        self.fk_controls = om.MSelectionList()
        self.ik_offsets = om.MSelectionList()
        self.ik_controls = om.MSelectionList()
        self.ik_fk_switch = om.MObject()
        self.joints = om.MObject()
        self.side = side

    # This creates a parent for the ik and fk joint chain which matches usually the pelvis, necessary because of the way
    # I set up the rig. Initially I set it up differently but that caused the rig to become destructive instead of
    # None destructive which is why I opted to add this method in the class.
    def create_joints_parent(self, joint=om.MObject(), string=''):
        """ Method to create an offset for the ik and fk chains
        :param joint: expects a joint in the form of an MObject. The joint should be the first joint in the chain that
        is used for the leg
        :param string: This is by default any empty string if used will add a subfix in the name of the created group
        :return: Returns the parent group that is created
        """
        dag_mod = om.MDagModifier()
        self.joints = dag_mod.createNode('transform')
        joint_name = om.MFnDependencyNode(joint).name()
        dag_mod.renameNode(self.joints, joint_name+'_'+string+names.joints)
        joints_transform = om.MFnTransform(om.MFnDagNode(self.joints).getPath())
        leg_parent = om.MFnDagNode(joint).parent(0)
        leg_parent_transform = om.MFnTransform(om.MFnDagNode(leg_parent).getPath())
        leg_parent_translate = leg_parent_transform.translation(4)
        leg_parent_rotate = leg_parent_transform.rotation(4, asQuaternion=True)
        leg_parent_scale = leg_parent_transform.scale()
        joints_transform.setTranslation(leg_parent_translate, 4)
        joints_transform.setRotation(leg_parent_rotate, 4)
        joints_transform.setScale(leg_parent_scale)
        dag_mod.reparentNode(self.joints, self.joint_group)
        dag_mod.doIt()
        return self.joints

    # This method will create an FK Chain from the already existing chain of which the first and last joint are selected
    # for creation
    def create_fk_chain(self, first_joint=om.MObject(), last_joint=om.MObject(), string=''):
        """ This creates and FK chain by getting the chain from the first and last joint variables.
        :param first_joint: Expects a joint in the form of an MObject
        :param last_joint: Expects a joint in the form of an MObject
        :param string: This is by default any empty string if used will add a subfix in the name of the created group
        :return: returns the created FK Chain
        """
        original_chain = self.get_chain(first_joint, last_joint)
        self.skinned_chain = original_chain
        dag_mod = om.MDagModifier()
        chain_it = om.MItSelectionList(original_chain)
        index = 0
        while not chain_it.isDone():
            joint = chain_it.getDependNode()
            fk_joint = dag_mod.createNode('joint')
            dag_mod.renameNode(fk_joint, om.MFnDependencyNode(joint).name()+'_'+string+names.fk)
            if index == 0:
                dag_mod.reparentNode(fk_joint, self.joints)
            if index != 0:
                dag_mod.reparentNode(fk_joint, self.fk_chain.getDependNode(index-1))
            joint_transform = om.MFnTransform(om.MFnDagNode(joint).getPath())
            new_joint_transform = om.MFnTransform(om.MFnDagNode(fk_joint).getPath())
            space = 1
            new_joint_transform.setTranslation(joint_transform.translation(space), space)
            new_joint_transform.setRotation(joint_transform.rotation(space, asQuaternion=True), space)
            self.fk_chain.add(fk_joint)
            index += 1
            chain_it.next()
        dag_mod.doIt()
        return self.fk_chain

    def create_ik_chain(self, first_joint=om.MObject(), last_joint=om.MObject(), string=''):
        """ This creates and IK chain by getting the chain from the first and last joint variables. The difference being
        that in this case the joint orients are used because non-zero joint orients are incompatible with the default
        ikHandle.
        :param first_joint: Expects a joint in the form of an MObject
        :param last_joint: Expects a joint in the form of an MObject
        :param string: This is by default any empty string if used will add a subfix in the name of the created group
        :return: returns the created IK Chain
        """
        original_chain = self.get_chain(first_joint, last_joint)
        self.skinned_chain = original_chain
        dag_mod = om.MDagModifier()
        chain_it = om.MItSelectionList(original_chain)
        index = 0
        while not chain_it.isDone():
            joint = chain_it.getDependNode()
            ik_joint = dag_mod.createNode('joint')
            dag_mod.renameNode(ik_joint, om.MFnDependencyNode(joint).name()+'_'+string+names.ik)
            if index == 0:
                dag_mod.reparentNode(ik_joint, self.joints)
            if index != 0:
                dag_mod.reparentNode(ik_joint, self.ik_chain.getDependNode(index-1))
            joint_transform = om.MFnTransform(om.MFnDagNode(joint).getPath())
            new_joint_transform = om.MFnTransform(om.MFnDagNode(ik_joint).getPath())
            new_joint_orient_plug = om.MFnDependencyNode(ik_joint).findPlug('jointOrient', True)
            space = 1
            new_joint_transform.setTranslation(joint_transform.translation(space), space)
            quaternion = joint_transform.rotation(space, asQuaternion=True)
            euler_rotation = quaternion.asEulerRotation()
            x_angle = om.MAngle(euler_rotation.x, 1)
            y_angle = om.MAngle(euler_rotation.y, 1)
            z_angle = om.MAngle(euler_rotation.z, 1)
            new_joint_orient_plug.child(0).setMAngle(x_angle)
            new_joint_orient_plug.child(1).setMAngle(y_angle)
            new_joint_orient_plug.child(2).setMAngle(z_angle)
            self.ik_chain.add(ik_joint)
            index += 1
            chain_it.next()
        dag_mod.doIt()
        self.ik_root = self.ik_chain.getDependNode(0)
        return self.ik_chain

    def create_ik_handle(self, start_joint=om.MObject(), last_joint=om.MObject(), pole_vector=om.MObject(),
                         limb=names.leg):
        """ Create ikHandle using the commands module and return the ikHandle as an MObject.
        :param start_joint: Start joint as MObject for the ikHandle
        :param last_joint: End joint as MObject for the ikHandle
        :param pole_vector: Pole Vector as MObject
        :param limb: String that is used for giving a name to  the ikHandle. Defaulted to the leg variable in the names
        module.
        :return:
        """
        if start_joint.isNull():
            start_joint = self.ik_chain.getDependNode(0)
        if last_joint.isNull():
            last_joint = self.ik_chain.getDependNode(self.ik_chain.length()-1)
        start_joint = om.MFnDependencyNode(start_joint).name()
        last_joint = om.MFnDependencyNode(last_joint).name()
        ik_handle_name = self.side+'_'+limb+'_'+names.ik_handle
        ik_handle = cmds.ikHandle(startJoint=start_joint, endEffector=last_joint, name=ik_handle_name)
        ik_sel = om.MSelectionList().add(ik_handle[0])
        self.ik_handle = ik_sel.getDependNode(0)
        dag_mod = om.MDagModifier()
        dag_mod.reparentNode(self.ik_handle, self.ik_group)
        dag_mod.doIt()
        if not pole_vector.isNull():
            pole_vector = om.MFnDagNode(pole_vector).fullPathName()
            cmds.poleVectorConstraint(pole_vector, ik_handle[0])
        return self.ik_handle

    def create_fk_controls(self, fk_chain=om.MSelectionList()):
        """ Creates FK controls using the default control defined in the names module.
        :param fk_chain: FK Chain in the form of an MSelectionList is expected. If no list is given the self.fk_chain
        variable will be used
        :return: Returns an MSelectionList containing the offsets and an MSelectionList containing the controls.
        Both are ordered in the same order.
        """
        if fk_chain.isEmpty():
            fk_chain = self.fk_chain
        fk_it = om.MItSelectionList(fk_chain)
        index = 0
        dag_mod = om.MDagModifier()
        while not fk_it.isDone():
            fk_joint = fk_it.getDependNode()
            ctrl = self.control_manager.create_control(object1=fk_joint)
            offset = self.control_manager.create_offset(ctrl)
            mesh = self.get_skinned_mesh(self.skinned_chain.getDependNode(0))
            self.fk_controls.add(ctrl)
            self.fk_offsets.add(offset)
            if index == 0:
                self.control_manager.match_control(fk_joint, offset)
            else:
                self.control_manager.match_control(fk_joint, offset, space=4)
            self.control_manager.resize_control(mesh, control=ctrl)
            self.control_manager.fit_control(fk_joint, scale=1)
            self.control_manager.match_control(fk_joint, offset, space=1)
            if index == 0:
                hip_parent = om.MFnDagNode(self.skinned_chain.getDependNode(0)).parent(0)
                fk_ctrl_parent = dag_mod.createNode('transform')
                dag_mod.renameNode(fk_ctrl_parent, self.side+'_'+names.leg+'_'+names.fk+'_'+names.offset)
                dag_mod.reparentNode(fk_ctrl_parent, self.control_group)
                hip_parent_transform = om.MFnTransform(om.MFnDagNode(hip_parent).getPath())
                fk_ctrl_parent_transform = om.MFnTransform(om.MFnDagNode(fk_ctrl_parent).getPath())
                fk_ctrl_parent_transform.setTransformation(hip_parent_transform.transformation())
                dag_mod.reparentNode(offset, fk_ctrl_parent)
                index += 1
                fk_it.next()
                continue
            dag_mod.reparentNode(offset, self.fk_controls.getDependNode(index-1))
            index += 1
            fk_it.next()

        dag_mod.doIt()
        return self.fk_offsets, self.fk_controls

    def create_ik_controls(self, control='', ik_chain=om.MSelectionList()):
        """ Creates IK controls using the default control defined in the names module.
        :param control: String is expected. This variable controls what type of control will be used for the IK Handle
        control
        :param ik_chain: MSelectionList containing the IK Chain is expected. If the list is empty the self.ik_chain
        variable will be used
        :return: Returns two MSelectionLists containing the offsets and containing the controls
        """
        if ik_chain.isEmpty():
            ik_chain = self.ik_chain
        if control == '':
            control = 'square_template.ma'
        dag_mod = om.MDagModifier()
        end_joint = ik_chain.getDependNode(ik_chain.length()-1)
        first_joint = ik_chain.getDependNode(0)
        second_joint = ik_chain.getDependNode(1)
        mesh = self.get_skinned_mesh(self.skinned_chain.getDependNode(self.skinned_chain.length()-1))
        helper = Helper()
        pv_point = helper.pole_vector_position(joint1=first_joint, joint2=second_joint, joint3=end_joint, mult=0.5)
        ik_control = self.control_manager.create_control(end_joint, control)
        ik_offset = self.control_manager.create_offset(ik_control)
        ik_match = dag_mod.createNode('locator')
        dag_mod.renameNode(ik_match, om.MFnDependencyNode(ik_control).name()+'_match')
        self.control_manager.match_control(end_joint, ik_offset, rotation=True)
        self.control_manager.resize_control(mesh)
        helper.straighten_rotation(ik_offset)
        pv_control = self.control_manager.create_control(object1=second_joint)
        pv_offset = self.control_manager.create_offset(pv_control)
        self.control_manager.match_control(second_joint, pv_offset, rotation=False)
        self.control_manager.resize_control(mesh, scale_modifier=1)
        self.control_manager.rename_control(pv_control, self.side+'_'+names.leg+'_pv_'+names.control)
        self.control_manager.rename_control(pv_offset, self.side+'_'+names.leg+'_pv_'+names.control+'_'+names.offset)
        om.MFnTransform(om.MFnDagNode(pv_offset).getPath()).setTranslation(pv_point, 4)
        dag_mod.reparentNode(pv_offset, self.control_group)
        dag_mod.reparentNode(ik_offset, self.control_group)
        inclusive_mat = om.MFnDagNode(end_joint).getPath().inclusiveMatrix()
        inclusive_mat_inverse = om.MFnDagNode(ik_control).getPath().inclusiveMatrixInverse()
        mat_diff = inclusive_mat * inclusive_mat_inverse
        om.MFnTransform(ik_match).setRotation(om.MTransformationMatrix(mat_diff).rotation(), 1)
        dag_mod.reparentNode(ik_match, ik_control)
        dag_mod.doIt()
        self.ik_offsets.add(ik_offset)
        self.ik_offsets.add(pv_offset)
        self.ik_controls.add(ik_match)
        self.ik_controls.add(pv_control)
        return self.ik_offsets, self.ik_controls

    def create_fk_nodes_and_connections(self, joint_chain=om.MSelectionList(), joint_controls=om.MSelectionList()):
        """ This method creates all the nodes and the connections needed for attaching the controls to the joints
        :param joint_chain: MSelectionList expected. The joint chain that the controls need to be connected to
        :param joint_controls: MSelectionList expected. The controls that will be connected to the joint chain
        :return: Nothing
        """
        if joint_chain.isEmpty():
            joint_chain = self.fk_chain
        if joint_controls.isEmpty():
            joint_controls = self.fk_controls
        helper = Helper()
        dg_mod = om.MDGModifier()
        index = 0
        fk_it = om.MItSelectionList(joint_chain)
        while not fk_it.isDone():
            fk_joint = fk_it.getDependNode()
            node_name = om.MFnDependencyNode(fk_it.getDependNode()).name()
            mult_matrix = dg_mod.createNode('multMatrix')
            decompose = dg_mod.createNode('decomposeMatrix')
            dg_mod.renameNode(mult_matrix, node_name+'_multMatrix')
            dg_mod.renameNode(decompose, node_name + '_mat_to_srt')
            control_output = helper.get_plug(joint_controls.getDependNode(index), 'worldMatrix')
            matrix_input = helper.get_plug(mult_matrix, 'matrixIn')
            matrix_output = helper.get_plug(mult_matrix, 'matrixSum')
            decompose_input = helper.get_plug(decompose, 'inputMatrix')
            decompose_rotate = helper.get_plug(decompose, 'outputRotate')
            decompose_translate = helper.get_plug(decompose, 'outputTranslate')
            decompose_scale = helper.get_plug(decompose, 'outputScale')
            fk_translate = helper.get_plug(fk_joint, 'translate')
            fk_rotate = helper.get_plug(fk_joint, 'rotate')
            fk_scale = helper.get_plug(fk_joint, 'scale')
            dg_mod.connect(control_output.elementByLogicalIndex(0), matrix_input.elementByLogicalIndex(0))
            if index == 0:
                offset = om.MFnDagNode(joint_controls.getDependNode(0)).parent(0)
                parent = om.MFnDagNode(offset).parent(0)
                parent_inverse_output = helper.get_plug(parent, 'worldInverseMatrix')
                dg_mod.connect(parent_inverse_output.elementByLogicalIndex(0), matrix_input.elementByLogicalIndex(1))
            if index != 0:
                parent_inverse_output = helper.get_plug(joint_controls.getDependNode(index-1), 'worldInverseMatrix')
                dg_mod.connect(parent_inverse_output.elementByLogicalIndex(0), matrix_input.elementByLogicalIndex(1))
            dg_mod.connect(matrix_output, decompose_input)
            dg_mod.connect(decompose_scale, fk_scale)
            dg_mod.connect(decompose_rotate, fk_rotate)
            dg_mod.connect(decompose_translate, fk_translate)
            dg_mod.doIt()
            index += 1
            fk_it.next()

    def create_ik_nodes_and_connections(self, ik_chain=om.MSelectionList(), ik_control=om.MObject(),
                                        ik_handle=om.MObject()):
        """ This method creates all the nodes and the connections needed for attaching the controls to the joints
        :param ik_chain: MSelectionList expected containing the joints in the IK Chain
        :param ik_control: MObject expected containing the control that will be attached to the IK Handle
        :param ik_handle: MObject containing the IK Handle
        :return: Nothing
        """
        if ik_control.isNull():
            ik_control = self.ik_controls.getDependNode(0)
        if ik_handle.isNull():
            ik_handle = self.ik_handle
        if ik_chain.isEmpty():
            ik_chain = self.ik_chain
        helper = Helper()
        dg_mod = om.MDGModifier()
        node_name = om.MFnDependencyNode(ik_chain.getDependNode(ik_chain.length() - 1)).name()
        mult_matrix = dg_mod.createNode('multMatrix')
        decompose_mult = dg_mod.createNode('decomposeMatrix')
        decompose = dg_mod.createNode('decomposeMatrix')
        ik_ctrl_output = helper.get_plug(ik_control, 'worldMatrix')
        parent_inverse_output = helper.get_plug(ik_chain.getDependNode(ik_chain.length()-2), 'worldInverseMatrix')
        matrix_input = helper.get_plug(mult_matrix, 'matrixIn')
        matrix_output = helper.get_plug(mult_matrix, 'matrixSum')
        decompose_input = helper.get_plug(decompose, 'inputMatrix')
        decompose_translate = helper.get_plug(decompose, 'outputTranslate')
        decompose_mult_input = helper.get_plug(decompose_mult, 'inputMatrix')
        decompose_mult_rotate = helper.get_plug(decompose_mult, 'outputRotate')
        ik_handle_translate = helper.get_plug(ik_handle, 'translate')
        ik_joint_rotate = helper.get_plug(ik_chain.getDependNode(ik_chain.length()-1), 'rotate')
        dg_mod.renameNode(mult_matrix, node_name+'_multMatrix')
        dg_mod.renameNode(decompose, om.MFnDependencyNode(ik_control).name()+'_world_to_srt')
        dg_mod.renameNode(decompose_mult, node_name+'_mat_to_srt')
        dg_mod.connect(ik_ctrl_output.elementByLogicalIndex(0), matrix_input.elementByLogicalIndex(0))
        dg_mod.connect(parent_inverse_output.elementByLogicalIndex(0), matrix_input.elementByLogicalIndex(1))
        dg_mod.connect(matrix_output, decompose_mult_input)
        dg_mod.connect(decompose_mult_rotate, ik_joint_rotate)
        dg_mod.connect(ik_ctrl_output.elementByLogicalIndex(0), decompose_input)
        dg_mod.connect(decompose_translate, ik_handle_translate)
        self.zero_joint_orient(ik_chain.getDependNode(ik_chain.length()-1))
        dg_mod.doIt()

    def create_ik_fk_switch(self, ik_controls=om.MSelectionList(), fk_controls=om.MSelectionList(), blend=False):
        """ Creates an IK FK switch in the form of an instanced NURBS curve with an IK attribute.
        :param ik_controls: MSelectionList containing all the IK controls
        :param fk_controls: MSelectionList containing all the FK controls
        :param blend: Boolean, if false will create an enum attribute, if true will create a float attribute
        :return:
        """
        if ik_controls.isEmpty():
            ik_controls = self.ik_controls
        if fk_controls.isEmpty():
            fk_controls = self.fk_controls
        helper = Helper()
        curve_point = om.MPointArray()
        curve_point.append(om.MPoint(0, 0, 0))
        curve_point.append(om.MPoint(0, 0, 0))
        double_array = om.MDoubleArray()
        double_array.append(0.0)
        double_array.append(0.0)
        dag_mod = om.MDagModifier()
        transform = dag_mod.createNode('transform')
        switch_curve = om.MFnNurbsCurve().create(curve_point, double_array, 1, 1, False, True, parent=transform)
        dag_mod.renameNode(switch_curve, self.side+'_leg_ikfk')
        attribute = om.MFnEnumAttribute().create('IKFK', 'IKFK')
        om.MFnEnumAttribute(attribute).addField('IK', 0)
        om.MFnEnumAttribute(attribute).addField('FK', 1)
        om.MFnEnumAttribute(attribute).keyable = True
        if blend is True:
            attribute = om.MFnNumericAttribute().create('IKFK', 'IKFK', 11)
            om.MFnNumericAttribute(attribute).setMin(0)
            om.MFnNumericAttribute(attribute).setMax(1)
            om.MFnNumericAttribute(attribute).keyable = True
        dag_mod.addAttribute(switch_curve, attribute)
        dag_mod.doIt()
        dg_mod = om.MDGModifier()
        ik_fk_reverse = dg_mod.createNode('reverse')
        dg_mod.renameNode(ik_fk_reverse, self.side+'_leg_ikfk_reverse')
        ikfk_plug = helper.get_plug(switch_curve, 'IKFK')
        reverse_input_x = helper.get_plug(ik_fk_reverse, 'inputX')
        reverse_output_x = helper.get_plug(ik_fk_reverse, 'outputX')
        dg_mod.connect(ikfk_plug, reverse_input_x)
        ik_ctrl_it = om.MItSelectionList(ik_controls)
        while not ik_ctrl_it.isDone():
            switch_curve_name = om.MFnDependencyNode(switch_curve).name()
            instance = cmds.instance(switch_curve_name)
            shape = cmds.listRelatives(instance, shapes=True, fullPath=True)[0]
            ik_ctrl = om.MFnDagNode(ik_ctrl_it.getDependNode()).fullPathName()
            ik_ctrl_dag_path = om.MFnDagNode(ik_ctrl_it.getDependNode()).getPath()
            if 'match' in ik_ctrl:
                ik_match = om.MFnDagNode(ik_ctrl_it.getDependNode())
                ik_ctrl_dag_path = om.MFnDagNode(ik_match.parent(0)).getPath()
                ik_ctrl = om.MFnDagNode(ik_match.parent(0)).fullPathName()
            cmds.parent(shape, ik_ctrl, relative=True, shape=True)
            cmds.delete(instance)
            ik_ctrl_dag_path.extendToShape(0)
            shape_vis = helper.get_plug(ik_ctrl_dag_path.node(), 'visibility')
            dg_mod.connect(reverse_output_x, shape_vis)
            ik_ctrl_it.next()
        fk_ctrl_it = om.MItSelectionList(fk_controls)
        while not fk_ctrl_it.isDone():
            switch_curve_name = om.MFnDependencyNode(switch_curve).name()
            instance = cmds.instance(switch_curve_name)
            if fk_ctrl_it.getDependNode() == self.fk_controls.getDependNode(self.fk_controls.length()-1):
                instance = om.MFnDependencyNode(transform).name()
            shape = cmds.listRelatives(instance, shapes=True, fullPath=True)[0]
            fk_ctrl = om.MFnDagNode(fk_ctrl_it.getDependNode()).fullPathName()
            cmds.parent(shape, fk_ctrl, relative=True, shape=True)
            cmds.delete(instance)
            fk_ctrl_dag_path = om.MFnDagNode(fk_ctrl_it.getDependNode()).getPath()
            fk_ctrl_dag_path.extendToShape(0)
            shape_vis = helper.get_plug(fk_ctrl_dag_path.node(), 'visibility')
            dg_mod.connect(reverse_input_x, shape_vis)
            fk_ctrl_it.next()
        dg_mod.doIt()
        self.ik_fk_switch = switch_curve
        return switch_curve

    def attach_to_skin_chain(self, ik_chain=om.MSelectionList(), fk_chain=om.MSelectionList(),
                             skin_chain=om.MSelectionList(), ik_fk_switch=om.MObject()):
        """ This method attaches the IK and FK Chains to the skinned joint chain
        :param ik_chain: MSelectionList containing the joints in the IK Chain
        :param fk_chain: MSelectionList containing the joints in the FK Chain
        :param skin_chain: MSelectionList containing the joints that are attached to the skincluster
        :param ik_fk_switch: MObject containing the object that the IK FK Switch is attached to
        :return:
        """
        if ik_chain.isEmpty():
            ik_chain = self.ik_chain
        if fk_chain.isEmpty():
            fk_chain = self.fk_chain
        if skin_chain.isEmpty():
            skin_chain = self.skinned_chain
        if ik_fk_switch.isNull():
            ik_fk_switch = self.ik_fk_switch
        helper = Helper()
        skin_chain_it = om.MItSelectionList(skin_chain)
        dg_mod = om.MDGModifier()
        index = 0
        while not skin_chain_it.isDone():
            current_node = skin_chain_it.getDependNode()
            current_node_name = om.MFnDependencyNode(current_node).name()
            blend = dg_mod.createNode('blendMatrix')
            mult_matrix = dg_mod.createNode('multMatrix')
            decompose = dg_mod.createNode('decomposeMatrix')
            ik_world = helper.get_plug(ik_chain.getDependNode(index), 'matrix')
            fk_world = helper.get_plug(fk_chain.getDependNode(index), 'matrix')
            blend_target = helper.get_plug(blend, 'target')
            blend_input = helper.get_plug(blend, 'inputMatrix')
            blend_output = helper.get_plug(blend, 'outputMatrix')
            ik_fk_attribute = helper.get_plug(ik_fk_switch, 'IKFK')
            decompose_input = helper.get_plug(decompose, 'inputMatrix')
            decompose_scale = helper.get_plug(decompose, 'outputScale')
            decompose_rotate = helper.get_plug(decompose, 'outputRotate')
            decompose_translate = helper.get_plug(decompose, 'outputTranslate')
            skin_scale = helper.get_plug(current_node, 'scale')
            skin_rotate = helper.get_plug(current_node, 'rotate')
            skin_translate = helper.get_plug(current_node, 'translate')
            blend_target_index = blend_target.elementByLogicalIndex(0)
            blend_target_input = blend_target_index.child(0)
            blend_target_weight = blend_target_index.child(2)
            dg_mod.connect(ik_world, blend_input)
            dg_mod.connect(fk_world, blend_target_input)
            dg_mod.connect(ik_fk_attribute, blend_target_weight)
            dg_mod.connect(blend_output, decompose_input)
            dg_mod.connect(decompose_scale, skin_scale)
            dg_mod.connect(decompose_rotate, skin_rotate)
            dg_mod.connect(decompose_translate, skin_translate)
            dg_mod.renameNode(blend, current_node_name+'_blendMatrix')
            dg_mod.renameNode(mult_matrix, current_node_name+'_blend_multMatrix')
            dg_mod.renameNode(decompose, current_node_name+'_blend_to_srt')
            index += 1
            skin_chain_it.next()
        dg_mod.doIt()

    def create_and_connect_messages(self):
        """ This method creates and connects the message attributes that are used for organising
        :return: nothing
        """
        helper = Helper()
        helper.add_and_connect_messages(self.ik_chain, self.ik_fk_switch, name=None)
        helper.add_and_connect_messages(self.fk_chain, self.ik_fk_switch, name=None)
        helper.add_and_connect_messages(self.skinned_chain, self.ik_fk_switch, name=None)
        helper.add_and_connect_messages(self.ik_controls, self.ik_fk_switch, name=None)
        helper.add_and_connect_messages(self.fk_controls, self.ik_fk_switch, name=None)
        helper.add_and_connect_messages(self.ik_handle, self.ik_fk_switch, name=None)
        helper.add_and_connect_messages(self.ik_fk_switch, self.root, name=None)
        helper.add_and_connect_messages(self.root, self.geo_group, name='Root')
        helper.add_and_connect_messages(self.root, self.ik_group, name='Root')
        helper.add_and_connect_messages(self.root, self.control_group, name='Root')
        helper.add_and_connect_messages(self.root, self.joint_group, name='Root')

    def get_ik_fk_switch(self, obj=om.MObject()):
        """ This method gets the ik_fk_switch from anyting that's connected to it through messages
        :param obj: MObject that's connected to ik_fk_switch
        :return: ik_fk_switch
        """
        helper = Helper()
        message_plug = helper.get_plug(obj, 'message')
        nodes = helper.get_plug_nodes(message_plug, 'message')
        for node in nodes:
            if 'ik' in om.MFnDependencyNode(node).name():
                self.ik_fk_switch = node
        return self.ik_fk_switch

    def get_root(self):
        """This method gets the root group
        :return: root group"""
        helper = Helper()
        message_plug = helper.get_plug(self.ik_fk_switch, 'message')
        nodes = helper.get_plug_nodes(message_plug, 'message')
        self.root = nodes[0]
        return self.root

    def get_groups(self):
        """ This method gets the groups and sets the variables should they be lost
        :return: Groups
        """
        helper = Helper()
        message_plug = helper.get_plug(self.root, 'message')
        nodes = helper.get_plug_nodes(message_plug, 'message')
        for node in nodes:
            node_name = om.MFnDependencyNode(node).name()
            if 'IK' in node_name:
                self.ik_group = node
            if 'GEO' in node_name:
                self.geo_group = node
            if 'CTRL' in node_name:
                self.control_group = node
            if 'JOINT' in node_name:
                self.joint_group = node
        return self.geo_group, self.ik_group, self.control_group, self.joint_group
