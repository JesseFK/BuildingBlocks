from controller_template import ControllerTemplate
from maya import cmds
from maya.api import OpenMaya as om
import names
from helper import Helper


# noinspection PyUnresolvedReferences
class ControllerManager(object):
    """
    This class manages the creation of controls and the offsets of these controls. Anything relating to the creation
    of controls will also be handled in this class.
    Most use cases of the number 4 will be referring to MSpace.kWorld = 4.
    """
    def __init__(self):
        self.manager = ControllerTemplate()
        self.manager.update_templates()
        self.controls = self.manager.get_controller_templates()
        self.default_control = None
        for control in self.controls:
            if control == names.default_control + '_template.ma':
                self.default_control = control
        self.control = om.MObject()
        self.offset = om.MObject()
        self.control_transform = om.MFnTransform()

    def create_control(self, object1, control=None, name=None):
        """ This method creates controls and uses the object1 variable for the name handling
        :param object1: MObject containing an object that the control will be created for
        :param control: String of the type of control that will be created
        :param name: String of alternative name if desired
        :return: returns the created control
        """
        if not control:
            control = self.default_control
        selection = om.MSelectionList()
        object1 = om.MObject(object1)
        object1_dag = om.MFnDagNode(object1)
        object1_name = object1_dag.name()
        if name is None:
            name = object1_name
        dag_mod = om.MDagModifier()
        control_import = self.manager.import_controller(ctrl_type=control)
        if control_import:
            control_import = control_import[0]
            selection.add(control_import)
            self.control = selection.getDependNode(0)
            dag_mod.renameNode(self.control, name+'_ctrl')
        dag_mod.doIt()
        return self.control

    def create_offset(self, control):
        """ Create an offset and parent object under offset
        :param control: MObject containing the control that will be parented under the offset
        :return: MObject containing the offset
        """
        control_dag = om.MFnDagNode(control)
        control_name = control_dag.name()
        dag_mod = om.MDagModifier()
        self.offset = dag_mod.createNode('transform')
        dag_mod.renameNode(self.offset, control_name + '_offset')
        dag_mod.reparentNode(control, self.offset)
        dag_mod.doIt()
        return self.offset

    def match_control(self, object1, control=None, rotation=True, space=4):
        """ This method will match the control in given space to the object
        :param object1: MObject containing object that control will be matched to
        :param control: MObject containing the control to be matched
        :param rotation: Boolean if rotation has to be matched
        :param space: The space to be used for setting the value. 4 is world and 2 is object.
        :return: MTransform of the control
        """
        if not control:
            control = self.control
        object1_dag_node = om.MFnDagNode(object1)
        control_dag_node = om.MFnDagNode(control)
        object1_dag_path = object1_dag_node.getPath()
        control_dag_path = control_dag_node.getPath()
        object1_transform = om.MFnTransform(object1_dag_path)
        control_transform = om.MFnTransform(control_dag_path)
        object1_translation = object1_transform.translation(space)
        object1_rotation = object1_transform.rotation(space, asQuaternion=True)
        control_transform.setTranslation(object1_translation, space)
        if rotation:
            control_transform.setRotation(object1_rotation, space)
        self.control_transform = control_transform
        return control_transform

    def resize_control(self, mesh=om.MObject(), control=None, scale_modifier=3):
        """ Resize the control based on the size of the mesh. While not foolproof should be good enough for most cases
        in terms of scaling
        :param mesh: MObject containing the mesh
        :param control: MObject containing the control
        :param scale_modifier: Modifier to increase the scale of the object, should the given result not be enough
        :return: MObject containing the control
        """
        control_transform = None
        if not control:
            control = self.control
            control_transform = self.control_transform
        elif control:
            control_dag_node = om.MFnDagNode(control)
            control_dag_path = control_dag_node.getPath()
            control_transform = om.MFnTransform(control_dag_path)
        else:
            return
        mesh = om.MFnMesh(om.MFnDagNode(mesh).getPath())
        bounding_box = om.MFnDagNode(control).boundingBox
        bounding_box_size = bounding_box.center.distanceTo(bounding_box.max)
        control_point = om.MPoint(control_transform.translation(4))
        closest_point = mesh.getClosestPoint(control_point, 4)
        mesh_distance = control_point.distanceTo(closest_point[0])
        scale = mesh_distance / bounding_box_size
        curve_iterator = om.MItGeometry(control)
        while not curve_iterator.isDone():
            curve_iterator.setPosition(curve_iterator.position() * (scale * scale_modifier))
            curve_iterator.next()
        return control

    def fit_control(self, joint=om.MObject(), control=None, scale=1):
        """ Fit this control to the size of the bone. This uses the joint, and it's first child to determine the size
        of the control
        :param joint: MObject containing the joint
        :param control: MObject containing the control
        :param scale: Scale modifier if somehow the control would end up being too small
        :return: Nothing
        """
        if not control:
            control = self.control
        length = Helper.get_joint_length(joint)
        curve_iterator = om.MItGeometry(control)
        bounding_box = om.MFnDagNode(control).boundingBox
        bounding_box_size = om.MFnDagNode(control).boundingBox.center.distanceTo(bounding_box.max)
        while not curve_iterator.isDone():
            position = curve_iterator.position()
            if curve_iterator.position().x > 0:
                if length == 0.0:
                    length = bounding_box_size
                new_position = om.MPoint((position.x - bounding_box_size + length) * scale, position.y, position.z, 1)
                curve_iterator.setPosition(new_position)
            elif curve_iterator.position().x < 0:
                bb_size = bounding_box_size * 0.5
                if length == 0.0:
                    bb_size = 0
                new_position = om.MPoint((position.x + bb_size) * scale, position.y, position.z, 1)
                curve_iterator.setPosition(new_position)
            curve_iterator.next()

    def rename_control(self, control=None, new_name=""):
        """ Rename the given control
        :param control: MObject containing the to be renamed control.
        :param new_name: String name to be given
        :return:
        """
        if not control:
            control = self.control
        dag_mod = om.MDagModifier()
        dag_mod.renameNode(control, new_name)
        dag_mod.doIt()
        return control
