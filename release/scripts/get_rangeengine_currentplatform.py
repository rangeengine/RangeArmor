import common as _common
from pathlib import Path
import platform
import sys 

args = _common.getArgs()
data = _common.getProjectData()

# RangeEngine Files #
defaultFiles_Windows = [
"RangeRuntime.exe",
"python3.dll",
"python310.dll",

"avcodec-58.dll",
"OpenAL32.dll",
"avdevice-58.dll",
"avformat-58.dll",
"avutil-56.dll",
"swresample-3.dll",
"swscale-5.dll",
"ucrtbase.dll",
"SDL2.dll",
]

defaultFiles_Linux = [
"RangeRuntime"
]

def main():
    # type: () -> None

    print("Started to copy range engine files")
    
    if data:
        _performRelease()


def _performRelease():
    # type: () -> None

    import os
    import shutil

    curPath = data["CurPath"]  # type: Path
    
    releaseDir = curPath / "release"  # type: Path
    
    if not releaseDir.exists():
        releaseDir.mkdir()
        print("> Directory of release created:", releaseDir.as_posix())
        
    engineDir = curPath / "engine"
    engineTargetDir = ""
    
    # Windows64
    if (platform.system() == "Windows" and platform.machine() == "AMD64"):
        engineTargetDir = engineDir / "Windows64"
    
    elif (platform.system() == "Windows" and platform.machine() == "AMD32"):
        engineTargetDir = engineDir / "Windows32"
        
    else:
        engineTargetDir = engineDir / "Linux64"
        
    # Clear target engine folder
    if engineTargetDir.exists():
        print("    > Removing existing directory:", engineTargetDir)
        shutil.rmtree(engineTargetDir.as_posix(), True)
    
    # Check if have the target engine folder
    if (not engineTargetDir.exists()):
        print("    > Creating directory: {}".format(engineTargetDir))
        engineTargetDir.mkdir()
        
    
    # "\2.79\python\bin\python.exe" = 27
    enginePath = Path(sys.executable[:-27]) # type: Path
    
    print("> Get the default files:")
    getFiles = defaultFiles_Windows if platform.system() == "Windows" else defaultFiles_Linux
    for file in getFiles:
        filePath = (enginePath / file)
        print("    > Copying {}".format(filePath))
        shutil.copy2(filePath.as_posix(), engineTargetDir.as_posix())
        
    # now, the 2.79 files #
    engineBundleTargetDir = engineTargetDir / "2.79"
    
    if (not engineBundleTargetDir.exists()):
        print("    > Creating directory: {}".format(engineBundleTargetDir))
        engineBundleTargetDir.mkdir()
    
    # 2.79/datafiles/gamecontroller #
    engineBundleDataFilesTargetDir = engineBundleTargetDir / "datafiles"
        
    datafilesPath = enginePath / "2.79/datafiles/gamecontroller"
    shutil.copytree(datafilesPath.as_posix(), engineBundleDataFilesTargetDir.as_posix())
    
    # 2.79/python # SLOW
    pythonpath = enginePath / "2.79/python"
    engineBundlePythonTargetDir = engineBundleTargetDir / "python"
    shutil.copytree(pythonpath.as_posix(), engineBundlePythonTargetDir.as_posix())
    
    print("    > Successful!")


try:
    main()
except Exception as e:
    print(e)
