#!/usr/bin/env python

help = """The script helps to convert C/C++ sources to C/C++ -like Python sources.

It does some simple edit operations like removing semicolons and type declarations.
After it you must edit code manually, but you'll probably spend less time doing it.
Example:

    if (a && b)               -->    if a and b:
    {                         -->        object.method()
        object->method();     -->
    }                         -->

The utility **will** make mistakes and **will not** generate ready for use code,
therefore it won't be useful for you unless you know both C/C++ and Python.

For better result, it is recomented to format your code to ANSI style
before doing conversion.

    astyle --style=ansi your.cpp source.cpp files.cpp

Usage:

    cpp2python.py DIR                     Find C/C++ files in the directory
                                          by suffix and process.
    cpp2python.py FILE                    Process the file.
    cpp2python.py -v|--version|-h|--help  Display the help message.

After the processing new file is created.
File name is {old file name with suffix}.py. i.e. main.cpp.py

Author: Andrei Kopats <hlamer@tut.by>
License: GPL
"""

import sys
import os.path
import re

class_lines = {'_function_':[]}
class_name = None

def is_source(filename):
    suffixes = ('.cpp', '.c', '.cxx', '.c++', '.cc', '.h', '.hpp', '.hxx', '.h++')
    for s in suffixes:
        if filename.endswith(s):
            return True
    return False

def process_line(line):
    global class_name

    """ remove semicolons

        codecode(param, param);
                V
        codecode(param, param)
    """
    line = re.sub(';([\r\n]?)$', '\\1', line) # remove semicolon from the end of line


    """ remove strings containing opening bracket

        if (blabla)
        {
            codecode
              V
        if (blabla)
            codecode
    """
    line = re.sub('\s*{\n$', '', line)

    """ remove closing brackets. Empty line preserved

        if (blabla)
        {
            codecode
              V
        if (blabla)
            codecode
    """
    line = re.sub('\s*}$', '', line)

    """ replace inline comment sign

        // here is comment
              V
        # here is comment
    """
    line = re.sub('//', '#', line)

    """ replace /* comment sign

        /* here is comment
              V
        ''' here is comment
    """
    line = re.sub('/\*', "'''", line)

    """ replace */ comment sign

        here is comment */
              V
        here is comment '''
    """
    line = re.sub('\*/', "'''", line)

    """ replace '||' with 'or'

        boolvar || anotherboolvar
              V
        boolvar or anotherboolvar
    """
    line = re.sub('\|\|', 'or', line)

    """ replace '&&' with 'and'

        boolvar && anotherboolvar
              V
        boolvar and anotherboolvar
    """
    line = re.sub('&&', 'and', line)

    """ replace '!' with 'not '

        if !boolvar
              V
        if not boolvar
    """
    line = re.sub('!([^=\n])', 'not \\1', line)

    """ replace '->' with '.'

        object->method()
              V
        object.method()
    """
    line = re.sub('->', '.', line)

    """ replace 'false' with 'False'

        b = false
              V
        b = False
    """
    line = re.sub('false', 'False', line)

    """ replace 'true' with 'True'

        b = true
              V
        b = True
    """
    line = re.sub('true', 'True', line)

    """ remove "const" word from the middle of string

        const int result = a.exec();
              V
        int result = a.exec();
    """
    line = re.sub('const ', ' ', line)

    """ remove "const" word from the end of string

        const int result = a.exec();
              V
        int result = a.exec();
    """
    line = re.sub(' const$', '', line)

    """ remove brackets around if statement and add colon

        if (i = 4)
              V
        if i = 4:
    """
    line = re.sub('if\s*\((.*)\)$', 'if \\1:', line)

    """ remove brackets around if statement and add colon

        if (i = 4)
              V
        if i = 4:
    """
    line = re.sub('if\s*\((.*)\)$', 'if \\1:', line)
    #return line

    """ remove type from method definition and add a colon and "def"

        -bool pMonkeyStudio::isSameFile( const QString& left, const QString& right )
        +pMonkeyStudio::isSameFile( const QString& left, const QString& right ):
    """

    matches = re.findall('^[\w:&<>\*]+\s+((\w+)::)?(\w+)\(([^\)]*\))$', line)
    if len(matches) > 0:
        class_name = matches[0][1]
        if not class_lines.has_key(class_name):
            class_lines[class_name] = []
        print class_name, matches
    line = re.sub('^[\w:&<>\*]+\s+([\w:]+)\(([^\)]*\))$', 'def \\1(self, \\2:', line)

    """ after previous replacement fix "(self, )" to "(self)"

        -def internal_projectCustomActionTriggered(self, ):
        +def internal_projectCustomActionTriggered(self):
    """
    line = re.sub('\(\s*self,\s*\)', '(self)', line)

    """ remove type name from function parameters (second and farther)

        -def internal_currentProjectChanged(self,  XUPProjectItem* currentProject, XUPProjectItem* previousProject ):
        +def internal_currentProjectChanged(self,  currentProject, previousProject ):
    """
    line = re.sub(',\s*[\w\d:&\*<>]+\s+([\w\d:&\*]+)', ', \\1', line)

    """ remove type name from variable declaration and initialisation
        -pAbstractChild* document = currentDocument()
        +document = currentDocument()
    """
    line = re.sub('[\w\d:&\*]+\s+([\w\d]+)\s*= ', '\\1 = ', line)

    """ remove class name from method definition

        -pMonkeyStudio::isSameFile( const QString& left, const QString& right ):
        +pMonkeyStudio::isSameFile( const QString& left, const QString& right ):
    """
    line = re.sub('^def [\w\d]+::([\w\d]+\([^\)]*\):)$', 'def \\1', line)

    """ replace '::' with '.'

        YourNameSpace::YourFunction(bla, bla)
              V
        YourNameSpace.YourFunction(bla, bla)
    """
    line = re.sub('::', '.', line)

    # remove & (reference opeartor or address-of opeartor)
    line = re.sub('&', '', line)

    """ replace 'else if' with 'elif'

        else if (blabla)
              V
        elif (blabla)
    """
    line = re.sub('else\s+if', 'elif', line)

    """ replace 'else' with 'else:'
        if blabala:
            pass
        else
            pass
              V
        if blabala:
            pass
        else:
            pass
    """
    line = re.sub('else\s*$', 'else:\n', line)

    """ Remove "new" keyword
        -i = new Class
        +i = Class
    """
    line = re.sub(' new ', ' ', line)

    """ Replace "this" with "self"
        -p = SomeClass(this)
        +p = SomeClass(self)
    """
    line = re.sub('([^\w])this([^\w])', '\\1self\\2', line)

    """ Replace Qt foreach macro with Python for
        -foreach ( QMdiSubWindow* window, a.subWindowList() )
        +foreach ( QMdiSubWindow* window, a.subWindowList() )
    """
    line = re.sub('foreach\s*\(\s*[\w\d:&\*]+\s+([\w\d]+)\s*,\s*([\w\d\.\(\)]+)\s*\)', 'for \\1 in \\2:', line)

    """ Replace Qt signal emit statement
        -emit signalName(param, param)
        +signalName.emit(param, param)
    """
    line = re.sub('emit ([\w\d]+)', '\\1.emit', line)

    """ Replace Qt connect call
        -connect( combo, SIGNAL( activated( int ) ), self, SLOT( comboBox_activated( int ) ) )
        +combo.activated.connect(self.comboBox_activated)
    """
    line = re.sub('connect\s*\(\s*([^,]+)\s*,\s*' + \
                'SIGNAL\s*\(\s*([\w\d]+)[^\)]+\)\s*\)\s*,'+ \
                '\s*([^,]+)\s*,\s*' + \
                'S[A-Z]+\s*\(\s*([\w\d]+)[^\)]+\)\s*\)\s*\)',
              '\\1.\\2.connect(\\3.\\4)', line)

    if class_name is not None:
        # because in above code there are many rules which will produce empty lines, and they will produce incorrect identation in generated code
        if len(line)>0:
            class_lines[class_name].append(line)
    else:
        class_lines['_function_'].append(line)

def process_file(in_filename, out_filename):
    """
    generator - outputs processed file
    """
    with open(in_filename, 'r') as file:
        lines = file.readlines()  # probably would die on sources more than 100 000 lines :D
    with open(out_filename, 'w+') as file:
        for line in lines:
            process_line(line)
        for c in class_lines.keys():
            file.write('class %s:\r\n' % c)
            for line in class_lines[c]:
                file.write('  '+line)
    print class_lines

def main():
    if '--help' in sys.argv or \
       '-h' in sys.argv or \
       '--version' in sys.argv or \
       '-v' in sys.argv:
        print(help)
        sys.exit(0)
    if len (sys.argv) != 2:
        print >> sys.stderr, 'Invalid parameters count. Must be 1'
        print(help)
        sys.exit(-1)
    if os.path.isdir(sys.argv[1]):
        for root, dirs, files in os.walk(sys.argv[1]):
            for file in files:
                in_filename = root + '/' + file
                if is_source(in_filename):
                    out_filename = in_filename + '.py' # not ideal
                    process_file(in_filename, out_filename)
    elif os.path.isfile(sys.argv[1]):
        process_file(sys.argv[1], sys.argv[1] + '.py')
    else:
        print >> sys.stderr, 'Not a file or directory', sys.argv[1]
        sys.exit(-1)

if __name__ == '__main__':
    main()
