import time
import names
from maya import cmds
from maya.api import OpenMaya as om
from helper import Helper


# I've decided to set this up with an already existing skeleton in mind. This means that I will make use of an already
# existing skeleton that is skinned to a mesh
class MasterComponent(object):
    """
    This is the master_component class which is used as a base class for other limbs
    Most use cases of the number 4 will be referring to MSpace.kWorld = 4
    """
    def __init__(self):
        self.root = om.MObject()
        self.skin_cluster = om.MObject()
        self.mesh = om.MObject()
        self.geo_group = om.MObject()
        self.joint_group = om.MObject()
        self.ik_group = om.MObject()
        self.control_group = om.MObject()

    # This method constructs the rig using the API and creates various groups that will be used to organise the rig
    def construct_rig(self, root_name=names.root_group):
        """ This method creates all the necessary groups that are used by the rig, and is essential for creating
        all other things in the rig. Since maya no longer requires unique names for groups and only for things
        that are in the same place in the hierarchy I've decided not to enforce unique names on the subgroups.
        :param root_name: String is expected, this will simply give a name to the root group.
        :return: Returns all created groups
        """
        dag_mod = om.MDagModifier()
        self.root = dag_mod.createNode('transform')
        self.geo_group = dag_mod.createNode('transform', parent=self.root)
        self.joint_group = dag_mod.createNode('transform', parent=self.root)
        self.control_group = dag_mod.createNode('transform', parent=self.root)
        self.ik_group = dag_mod.createNode('transform', parent=self.root)
        dag_mod.renameNode(self.root, root_name)
        dag_mod.renameNode(self.control_group, names.control_group)
        dag_mod.renameNode(self.ik_group, names.ik_group)
        dag_mod.renameNode(self.joint_group, names.joint_group)
        dag_mod.renameNode(self.geo_group, names.geo_group)
        dag_mod.doIt()
        return self.root, self.geo_group, self.joint_group, self.control_group, self.ik_group

    # This is a method for getting the skincluster from joint object
    def get_skin_cluster(self, joint):
        """ This method gets the skincluster of the given joint. It makes use of the helper class to get nodes that
        are connected to a certain plug. In this case "lockInfluenceWeights"
        :param joint: Expects a joint in the form of an MObject
        :return: returns the skincluster as an MObject
        """
        message_attr = om.MFnDependencyNode(joint).attribute('message')
        joint_plug = om.MPlug(joint, message_attr)
        skin_cluster = Helper.get_plug_nodes(joint_plug, plug_name='lockInfluenceWeights', source=False)
        self.skin_cluster = skin_cluster[0]
        return self.skin_cluster

    # This is a method for getting the mesh from the joint, it uses the get skincluster method
    def get_skinned_mesh(self, joint):
        """ This gets the mesh as an MObject using the helper class and a given joint that is skinned to that mesh
        :param joint: Expects a joint connect to a skincluster so that the mesh can be retrieved
        :return: returns the mesh as an MObject
        """
        skin_cluster = self.get_skin_cluster(joint)
        mesh = Helper.get_attached_node(skin_cluster, 296, om.MItDependencyGraph.kDownstream)
        self.mesh = mesh
        return self.mesh

    # Static method to get all the joints in between the two variables
    @staticmethod
    def get_chain(first=om.MObject(), last=om.MObject()):
        """ This method gets all things in the hierarchy between variable first and last
        :param first: Usually a joint in the form of an MObject
        :param last: Usually a joint in the form of an MObject
        :return: returns the retrieved chain of joints
        """
        chain = om.MSelectionList()
        dag_it = om.MItDag().reset(first)
        while not dag_it.isDone():
            chain.add(dag_it.currentItem())
            if dag_it.currentItem() == last:
                break
            dag_it.next()
        return chain

    @staticmethod
    def get_all_children(first=om.MObject()):
        """ This method gets all things in the hierarchy below variable joint
        :param first: Usually a joint in the form of an MObject
        :return: returns the retrieved chain of joints
        """
        chain = om.MSelectionList()
        dag_it = om.MItDag().reset(first)
        while not dag_it.isDone():
            chain.add(dag_it.currentItem())
            dag_it.next()
        return chain

    # This method makes a chain out of un-parented joints
    @staticmethod
    def parent_chain(chain=om.MSelectionList()):
        """ Parents all objects in the chain under each other to form a joint chain
        :param chain: Expects an MSelectionList containing the to be parented items
        :return: returns the same chain variable in the form of an MSelectionList
        """
        chain_it = om.MItSelectionList(chain)
        dag_mod = om.MDagModifier()
        index = 0
        while not chain_it.isDone():
            if index == 0:
                chain_it.next()
                continue
            dag_mod.reparentNode(chain_it.getDependNode(), chain.getDependNode(index-1))
            index += 1
            chain_it.next()
        dag_mod.doIt()
        return chain

    # Method to zero out joint orient attributes
    @staticmethod
    def zero_joint_orient(joint=om.MObject()):
        """ This method uses the helper class to get the jointOrient plugs and uses empty MAngle objects to set those
        plug values to 0
        :param joint: The joint as an MObject that wants their orient zeroed
        :return: returns the jointOrient attribute plug as an MPlug
        """
        helper = Helper()
        m_angle = om.MAngle()
        joint_x = helper.get_plug(joint, 'jointOrientX')
        joint_y = helper.get_plug(joint, 'jointOrientY')
        joint_z = helper.get_plug(joint, 'jointOrientZ')
        joint_x.setMAngle(m_angle)
        joint_y.setMAngle(m_angle)
        joint_z.setMAngle(m_angle)
        return helper.get_plug(joint, 'jointOrient')
