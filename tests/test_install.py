import os
import sys
import scripttest

# Locate get-pip.py relative to this test file
GET_PIP = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       'get-pip.py')

# Handle platform specific differences
if sys.platform.startswith('win'):
    BIN_DIR = 'Scripts'
    def exe_base(path):
        """Command name of an executable"""
        return os.path.splitext(os.path.basename(path))[0]
else:
    BIN_DIR = 'bin'
    def exe_base(path):
        """Command name of an executable"""
        return os.path.basename(path)


def test_install(tmpdir):
    """Simple test that installing pip using get-pip works"""

    # Create a scripttest environment
    env = scripttest.TestFileEnvironment(tmpdir / 'env')

    # Create a virtual environment with no pip present.
    # TODO: add the following cases
    #   1. environment name with spaces
    #   2. environment with some version of pip already present

    ve_name = 've'
    env.run('virtualenv', '--no-pip', '--no-setuptools', '--no-wheel',
            ve_name)
    ve_python = os.path.join(ve_name, BIN_DIR, 'python')

    # Run get-pip.py from this repository
    result = env.run(ve_python, GET_PIP)

    # Check if the pip command was created
    created_pip = None
    for name, file_obj in result.files_created.items():
        if exe_base(name) == 'pip' and file_obj.file:
            created_pip = file_obj
            break
    assert created_pip

    # Confirm that both the pip exe and python -m pip work
    env.run(created_pip.full, '--version')
    env.run(ve_python, '-m', 'pip', '--version')
