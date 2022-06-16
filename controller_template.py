import os
import sys
from maya import cmds
from maya import mel
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
            name = line_split[-1].strip().rstrip('";\n').lstrip('"')
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
                control_file = open(self.path+name, 'r')
                lines = control_file.readlines()
                concatenated_lines = []
                node_lines = lines[5:-1]
                list_length = len(node_lines)
                line_number = 0
                new_line = ''
                while not line_number == list_length:
                    raw_line = r'{}'.format(node_lines[line_number])
                    if raw_line.strip() == ';':
                        new_line += raw_line
                        concatenated_lines.append(new_line)
                        new_line = ''
                    elif ';' in raw_line:
                        concatenated_lines.append(raw_line)
                    elif ';' not in raw_line:
                        new_line += raw_line
                    line_number += 1
                control_transform = ''
                result = None
                for command in concatenated_lines:
                    if 'uid' in command.strip():
                        pass
                    else:
                        if 'template' in command and 'Shape' in command:
                            new_command = command.split('-p')[0]+'-p "'+control_transform+'" ;'
                            mel.eval(new_command.strip())
                        else:
                            result = mel.eval(command.strip())
                    if result is not None:
                        if 'template' in result and 'Shape' not in result:
                            control_transform = result
                            control.append(result)
                open(self.path+name, 'r').close()
        control = list(set(control))
        if len(control) < 2:
            return control
        else:
            return control
