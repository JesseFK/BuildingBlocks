import os
import sys
from maya import cmds
import names


# This class makes use of a file called __templates__.ma which contains all my controls that I've made. It then parses
# that file and creates new maya ascii files that be imported as new controls.
class ControllerTemplate(object):
    """ This class constructs a template for NURBS curve controllers. The '__init__' method simply constructs the path
    and the template
    file name.
    """
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.path = self.base_path+'/controllers/'
        self.template = names.controller_templates

    def update_templates(self):
        """ This method will update all the template files (except for '__templates__'). It will create new files
        if previously they did not exist.
        """
        template_file = open(self.path + self.template + '.ma', 'r')
        lines = template_file.readlines()
        line_numbers = []
        for line in enumerate(lines):
            if 'transform' in line[1] and 'template' in line[1]:
                line_numbers.append(line[0])
            elif 'createNode lightLinker' in line[1]:
                line_numbers.append(line[0])
        ctrl_names = []
        for num in line_numbers:
            line_split = lines[num].split(' ')
            name = line_split[-1].rstrip('";\n').lstrip('"')
            if 'lightLinker' in name:
                pass
            else:
                ctrl_names.append(name)
        for i in enumerate(zip(line_numbers, ctrl_names)):
            start = line_numbers[i[0]]
            if i[0] == len(line_numbers):
                break
            end = line_numbers[i[0]+1]
            open(self.path + i[1][1] + '.ma', 'w').close()
            new_file = open(self.path + i[1][1] + '.ma', 'w')
            new_file.writelines(lines[0])
            new_file.write('//Name: ' + str(i[1][1]) + '.ma\n')
            new_file.writelines(lines[2:5])
            new_file.writelines(lines[start:end])
            new_file.write('// End of ' + str(i[1][1]) + '.ma\n')
            new_file.close()

    def get_controller_templates(self):
        """ This method lists all the files in the directory, except the '__templates__' file. It will then return that
        list.
        :return: List of the files that contain the NURBS controllers.
        """
        controllers = []
        directory = os.listdir(self.path.rstrip('/'))
        for template in directory:
            if self.template.rstrip('__') in template:
                pass
            else:
                controllers.append(template)
        return controllers

    def import_controller(self, ctrl_type='square'):
        """ Import controller from created template.ma files
        :param ctrl_type: Type is a string argument that will look for that controller in the files, if there's nothing
        that matches it does nothing.
        """
        control = []
        for name in os.listdir(self.path):
            if ctrl_type in self.template:
                cmds.warning("Can't import default file")
                break
            if ctrl_type in str(name):
                imp = cmds.file(self.path+name, i=True, rnn=True)
                control.append(imp)
        if len(control) < 2:
            return control
        else:
            return control
