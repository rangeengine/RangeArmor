import zlib
import base64

from pathlib import Path

rootPath = Path(__file__).parent.parent.parent
launcherPath = rootPath / "release/launcher/launcher.py"

launcherHeader = '''
from base64 import b64decode as bng34i8g349ng3948n2f
from zlib import decompress as plioknwef2n902349209n
jhfgd90i34gniorfg93n4girbng903=exec
imnv34908inv34908v2349m0g4="""'''

launcherFooter = '''"""
jhfgd90i34gniorfg93n4girbng903(plioknwef2n902349209n(bng34i8g349ng3948n2f(imnv34908inv34908v2349m0g4.encode())).decode())
'''

if launcherPath.exists():
    launcherData = None # type: str
    
    with open(launcherPath.as_posix(), "r") as openedFile:
        launcherData = openedFile.read()
    
    with open(launcherPath.as_posix(), "w") as openedFile:
        launcherContent = base64.b64encode(zlib.compress(launcherData.encode())).decode()
        openedFile.write(launcherHeader + launcherContent + launcherFooter)
        print("> Encoded launcher script:", openedFile.name)
        
else:
    print("X Launcher script not found:", launcherPath.as_posix())
