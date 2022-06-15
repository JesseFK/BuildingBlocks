from maya import cmds
from maya.api import OpenMaya as om
import names
import math


# This is a helper class that contains various commonly used by me methods
class Helper(object):
    """This class contains several methods that are used during the construction of various parts of the rig"""
    @staticmethod
    def get_attached_node(m_obj, node_type, direction=om.MItDependencyGraph.kUpstream,
                          level=om.MItDependencyGraph.kPlugLevel):
        """ This gets the node attached to the MObject of the node type that is asked
        MFn class documentation dictates that:
        kIkHandle = 120
        kMesh = 296
        kJoint = 121
        :param m_obj: MObject that you want attached node of
        :param node_type: The type of node you want to get
        :param direction: The direction in which should be searched, either upstream or downstream
        :param level: The level that you want to search for (e.g. plug level or node level)
        :return: Returns the attached node
        """
        depend_it = om.MItDependencyGraph(m_obj, direction, level=level)
        node = None
        while not depend_it.isDone():
            if depend_it.currentNode().apiType() == node_type:
                node = depend_it.currentNode()
                break
            depend_it.next()
        return node

    @staticmethod
    def get_plug(obj, plug_name='message'):
        """ Get plug name of specified object
        :param obj: MObject that you want the plug of
        :param plug_name: Plug name that you want, which is usually just the attribute name
        :return: Returns MPlug of the asked plug
        """
        dep_node = om.MFnDependencyNode(obj)
        return dep_node.findPlug(plug_name, True)

    @staticmethod
    def get_plug_nodes(plug, plug_name='message', source=True, destinations=True):
        """ Get nodes that are attached to certain plug
        :param plug: MPlug
        :param plug_name: Plug node that other nodes are attached to
        :param source: Boolean if true also gets sources that are attached to plug
        :param destinations: Boolean if true also gets destinations that are attached to plug
        :return: Returns list of nodes that are attached to attributes
        """
        dep_node = om.MFnDependencyNode(plug.node())
        msg_plug = dep_node.findPlug(plug_name, False)
        if source == True and destinations == True:
            return [plug.node() for plug in msg_plug.destinations()] + [msg_plug.source().node()]
        elif source == True and destinations == False:
            return [msg_plug.source().node()]
        elif source == False and destinations == True:
            return [plug.node() for plug in msg_plug.destinations()]

    # Distance between two vectors
    @staticmethod
    def distance_between(vector1, vector2):
        """ Gets distance between two vectors
        :param vector1: A vector 3
        :param vector2: A vector 3
        :return: Returns distance as a float
        """
        p1, p2, p3 = vector1[0], vector1[1], vector1[2]
        q1, q2, q3 = vector2[0], vector2[1], vector2[2]
        return math.sqrt(((p1 - q1) ** 2) + ((p2 - q2) ** 2) + ((p3 - q3) ** 2))

    @staticmethod
    def get_joint_length(joint):
        """ Gets the length of specified joint to its child
        :param joint: MObject containing the joint
        :return: Joint length as float
        """
        dag_node = om.MFnDagNode(joint)
        if dag_node.childCount() < 1:
            return float(0)
        joint_child = dag_node.child(0)
        child_dag_node = om.MFnDagNode(joint_child)
        joint_transform = om.MFnTransform(dag_node.getPath())
        child_transform = om.MFnTransform(child_dag_node.getPath())
        joint_translation = joint_transform.translation(4)
        child_translation = child_transform.translation(4)
        joint_length = om.MPoint(joint_translation).distanceTo(om.MPoint(child_translation))
        return joint_length

    @staticmethod
    def get_point(m_obj, vector=False, space=om.MSpace.kWorld):
        """ Get point of object translation in specified space
        :param m_obj: MObject of object that you want the point of
        :param vector: Boolean if false will return MPoint else will return MVector
        :param space: Space in which to get the point, om.MSpace.kWorld = 4
        :return: returns either MPoint or MVector
        """
        dag_node = om.MFnDagNode(m_obj)
        transform = om.MFnTransform(dag_node.getPath())
        m_vec = transform.translation(space)
        if vector is False:
            return om.MPoint(m_vec)
        else:
            return m_vec

    def pole_vector_position(self, joint1, joint2, joint3, mult=1):
        """ Calculates the pole vector position using three points
        :param joint1: MObject containing joint
        :param joint2: MObject containing joint
        :param joint3: MObject containing joint
        :param mult: Multiplier if the distance from the leg is not the desired distance
        :return: returns pole vector position as MVector
        """
        shoulder_point = self.get_point(joint1, True)
        elbow_point = self.get_point(joint2, True)
        wrist_point = self.get_point(joint3, True)
        shoulder_to_wrist = wrist_point - shoulder_point
        shoulder_to_elbow = elbow_point - shoulder_point
        scale = (shoulder_to_wrist * shoulder_to_elbow) / (shoulder_to_wrist * shoulder_to_wrist)
        projected_point = shoulder_to_wrist * scale + shoulder_point
        arm_length = self.distance_between(shoulder_point, elbow_point) + self.distance_between(elbow_point, wrist_point)
        return ((elbow_point - projected_point).normal() * arm_length * mult) + elbow_point

    @staticmethod
    def match_transforms(object1=om.MObject(), object2=om.MObject()):
        """ Match transform of one object to another
        :param object1: MObject containing desired object to be matched
        :param object2: MObject containing object to be matched to
        :return: MTransform of the second object
        """
        object1_dag_node = om.MFnDagNode(object1)
        object2_dag_node = om.MFnDagNode(object2)
        object1_dag_path = object1_dag_node.getPath()
        object2_dag_path = object2_dag_node.getPath()
        object1_transform = om.MFnTransform(object1_dag_path)
        object2_transform = om.MFnTransform(object2_dag_path)
        object1_translation = object1_transform.translation(4)
        object1_rotation = object1_transform.rotation(4, asQuaternion=True)
        object2_transform.setTranslation(object1_translation, 4)
        object2_transform.setRotation(object1_rotation, 4)
        return object2_transform

    @staticmethod
    def compare_radians(value):
        """ Method that checks if radians fall within a ranged and then returns a straightened out value
        :param value: Value in radians
        :return: Straightened value in radians
        """
        if 0.785398 < value < 1.5708:
            value = 1.5708
        elif -0.785398 > value > -1.5708:
            value = -1.5708
        elif 0 < value < 0.785398:
            value = 0
        elif -0.785398 < value < 0:
            value = 0
        elif 1.5708 < value < 3.1415:
            value = 1.5708
        elif -1.5708 > value > -3.1415:
            value = -1.5708
        elif 3.1415 < value < 4.71239:
            value = 3.1415
        elif -3.1415 > value > -4.71239:
            value = -3.1415
        elif 3.1415 < value < 4.71239:
            value = 0
        return value

    def straighten_rotation(self, obj=om.MObject()):
        """ Straighten rotation of object meaning that the object will appear straight in some plane in the world
        :param obj: MObject containing objected to be straightened
        :return: MEulerRotation containing the new rotation values
        """
        dag_node = om.MFnDagNode(obj)
        dag_path = dag_node.getPath()
        obj_transform = om.MFnTransform(dag_path)
        quaternion = obj_transform.rotation(4, asQuaternion=True)
        x = quaternion.asEulerRotation().x
        y = quaternion.asEulerRotation().y
        z = quaternion.asEulerRotation().z
        new_x = self.compare_radians(x)
        new_y = self.compare_radians(y)
        new_z = self.compare_radians(z)
        new_rot = om.MEulerRotation(new_x, new_y, new_z)
        obj_transform.setRotation(new_rot, 1)
        return new_rot

    def add_and_connect_messages(self, to_connect, to_connect_to=om.MObject, name=None):
        """ This method can add and connect message attributes to an object from another object.
        The to connect attribute can be an MObject or an MSelectionList
        :param to_connect: MObject or MSelectionList
        :param to_connect_to: MObject
        :param name: String, optional name to give to the attribute
        :return:
        """
        dag_mod = om.MDagModifier()
        if isinstance(to_connect, om.MObject):
            if name is None:
                name = om.MFnDependencyNode(to_connect).name()
            new_message = om.MFnMessageAttribute().create(name, name)
            message = self.get_plug(to_connect, 'message')
            dag_mod.addAttribute(to_connect_to, new_message)
            new_message = om.MPlug(to_connect_to, new_message)
            dag_mod.connect(message, new_message)
            dag_mod.doIt()
        elif isinstance(to_connect, om.MSelectionList):
            sel_it = om.MItSelectionList(to_connect)
            while not sel_it.isDone():
                name = om.MFnDependencyNode(sel_it.getDependNode()).name()
                new_message = om.MFnMessageAttribute().create(name, name)
                message = self.get_plug(sel_it.getDependNode(), 'message')
                dag_mod.addAttribute(to_connect_to, new_message)
                new_message = om.MPlug(to_connect_to, new_message)
                dag_mod.connect(message, new_message)
                dag_mod.doIt()
                sel_it.next()
        else:
            print("Method not compatible")

    @staticmethod
    def get_root_joints():
        dag_it = om.MItDag()
        root_joint_list = om.MSelectionList()
        while not dag_it.isDone():
            print dag_it.getPath().apiType(), dag_it.depth()
            if dag_it.depth() > 1:
                dag_it.next()
            else:
                dag_path = dag_it.getPath()
                print dag_path.apiType()
                if dag_path.apiType() == 121:
                    root_joint_list.add(dag_it.currentItem())
                dag_it.next()
        return root_joint_list
