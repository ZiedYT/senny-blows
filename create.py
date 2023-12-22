import os
import shutil 
from threading import Thread
import subprocess
def installer(path):
    os.system("pyinstaller "+path)

if(os.path.isdir("dist")):
    shutil.rmtree("dist")

installer("sennyblows.spec")

shutil.copy("icon.png", "dist/sennyblows/icon.png")
shutil.copy("main.ui", "dist/sennyblows/main.ui")
shutil.copytree("drivers","dist/sennyblows/drivers")
shutil.copy("dist/sennyblows/sennyblows.exe", "dist/sennyblows/sennyblows_console.exe")
shutil.make_archive("dist/sennyblows", 'zip', "dist/sennyblows")