# coding: utf-8
"""
Write a markdown documentation file for command line scripts.
"""
import importlib
import subprocess
from glob import glob
import os.path
import sys


FOLDER_DOC = os.path.join('..', '..', 'telemac_toolbox.wiki')

FOLDER_SCRIPTS = os.path.join('..')


if __name__ == "__main__":
    # Build sorted list of CLI scripts
    with open(os.path.join(FOLDER_DOC, '_Sidebar.md'), 'w') as out_sidebar:
        with open(os.path.join(FOLDER_DOC, 'Home.md'), 'w') as out_home:
            for file_path in sorted(glob(os.path.join(FOLDER_SCRIPTS, '*.py'))):
                script_name = os.path.splitext(os.path.basename(file_path))[0]
                print(script_name)

                out_sidebar.write('* [[%s]]\n' % script_name)
                out_home.write('* [[%s]]\n' % script_name)

                with open(os.path.join(FOLDER_DOC, script_name + '.md'), 'w', encoding='utf8') as fileout:
                    fileout.write('```\n')
                    fileout.flush()
                    subprocess.run(['python', file_path, '-h'], stdout=fileout)
                    fileout.flush()
                    fileout.write('```\n')
