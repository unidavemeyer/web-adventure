# example of finding things on the path

import os
import subprocess

def PathFind(strExe):
    strPath = os.environ.get('PATH', None)
    lStrPath = strPath.split(':')
    for strPath in lStrPath:
        strCheck = os.path.join(strPath, strExe)
        if os.path.exists(strCheck):
            return strCheck

    return None

def RunWithPython(lStrArg):
    pathPython = PathFind('python3')
    lStrExec = [pathPython]
    lStrExec.extend(lStrArg)
    print(f"Running {lStrExec}")

    bOut = subprocess.check_output(lStrExec, stderr=subprocess.STDOUT)
    print(bOut.decode('utf-8'))

if __name__ == '__main__':

    pathPython = PathFind('python3')
    print(f"Path to python3: {pathPython}")

    RunWithPython(["hello.py", "arg1"])
