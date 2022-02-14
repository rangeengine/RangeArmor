import zlib
import os
import sys
import string
import shutil
import glob
import base64
import subprocess
import platform

from pathlib import Path
from ast import literal_eval
from time import time, sleep
from hashlib import md5

_DEBUG = False
PLAT_QUOTE = '"' if platform.system() == "Windows" else "'"
ITEM_SEPARATOR = "\t"

curPath = Path(__file__).resolve().parent
rootPath = curPath.parent
curPlatform = platform.system()


if curPath.name == "source":
    curPath = curPath.parent / "launcher"
    os.chdir(curPath.as_posix())


def debugMsg(*args, waitInput=True):
    # type: (object, bool) -> None
    
    if _DEBUG:
        finalMsg = ""
        for arg in args: finalMsg += str(arg)
        print(finalMsg)
        if waitInput: input("Press any key to continue...")


def loadConfig(path):
    # type: (Path) -> None
    
    config = None
    configPath = path / "config.json"
    engineCandidates = [curPlatform, curPlatform + "32", curPlatform + "64"]
    enginePath = None
    
    for _path in engineCandidates:
        _path = path / (_path + "/engine_executable.txt")
        
        if _path.exists():
            _path = _path.resolve()
            
            with open(_path.as_posix(), "r") as sourceFile:
                enginePathRead = rootPath / literal_eval(sourceFile.read().split('=')[-1]) # type: Path
                
                if enginePathRead.exists():
                    enginePath = enginePathRead
                    break
    
    if configPath.exists():
        
        with open(configPath.as_posix(), "r") as sourceFile:
            config = literal_eval(sourceFile.read())
            print("> Read config from", configPath.as_posix())
            
        if enginePath and enginePath.exists():
                config["EnginePath"] = enginePath.as_posix()
                print("> Read engine path from", enginePath.as_posix())
                return config
                
        else:
            print("X Could not find suitable engine executable")
                
    else:
        print("X Could not find config file at", configPath)


def getGameDir(config):
    # type: (dict[str, object]) -> Path
    
    def getGameDirName(name):
        # type: (str) -> str
        
        result = ""
        allowedChars = string.ascii_lowercase + string.ascii_uppercase + " -"
        for c in name:
            if c in allowedChars:
                result += c
        return result
        
    gameDir = Path.home()
    gameName = getGameDirName(config["GameName"])
    
    # Get game directory in a cross platform way
    if sys.platform == "win32":
        gameDir = Path(os.environ.get("APPDATA")) / gameName
    elif sys.platform == "linux":
        gameDir = gameDir / (".local/share/" + gameName)
        
    # Create game directory
    gameDir.mkdir(parents=True, exist_ok=True)
        
    return gameDir


def getTempDir(config):
    # type: (dict[str, object]) -> Path
    
    tempDir = Path.home()
    tempDirName = md5(("BGArmor" + str(time())).encode()).hexdigest().upper()
    
    if sys.platform == "win32":
        tempDir = Path(os.environ.get("TEMP")) / tempDirName
    elif sys.platform == "linux":
        tempDir = Path("/tmp/." + tempDirName)
        
    tempDir.mkdir(parents=False, exist_ok=True)
    
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(tempDir.as_posix(), 2)
        
    return tempDir


def getFilesLists(path):
    # type: (Path) -> list[list[Path]]
    
    persistentFiles = []
    generalFiles = []
    
    # Populate persistent files list
    for pattern in config["Persistent"]:
        persistentFiles += [Path(p).resolve() for p in glob.glob(
            path.as_posix() + "/**/" + pattern, recursive=True)]
    
    # Populate general files list
    generalFiles += [Path(p).resolve() for p in glob.glob(
            path.as_posix() + "/**/*", recursive=True)
            if Path(p).is_file()]
    
    # Remove persistent files from general files list
    for pers in persistentFiles:
        for gen in generalFiles:
            if pers.samefile(gen):
                generalFiles.remove(gen)
                
    return [persistentFiles, generalFiles]


def ensurePath(path):
    # type: (Path) -> Path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def decompressDataFile(dataFile, targetPath):
    # type: (Path, Path) -> None
    
    startTime = time()
    
    if dataFile.exists():
        curLineType = "Path"
        filePath = None
        numChunks = 1
        curChunk = 0
        print("\n> Decompressing data file from", dataFile.as_posix())
        
        for line in open(dataFile.as_posix(), "rb"):
            if curLineType == "Path":
                lineItems = base64.b64decode(line)
                lineItems = lineItems.decode()
                lineItems = lineItems.split(ITEM_SEPARATOR)
                filePath = (targetPath / lineItems[0])
                numChunks = literal_eval(lineItems[1])
                curLineType = "Data"
                
            else:
                if not filePath.parent.exists():
                    try:
                        os.makedirs(filePath.parent.as_posix())
                    except:
                        pass
                        
                if curChunk < numChunks:
                    with open(filePath.as_posix(), "ab") as targetFileObj:
                            targetFileObj.write(zlib.decompress(base64.b64decode(line)))
                            curChunk += 1
                        
                if curChunk >= numChunks:
                    curChunk = 0
                    numChunks = 1
                    curLineType = "Path"
                
    print("> Done! Time taken:", round(time() - startTime, 3), "seconds\n")


def copyPersistentFiles(pathFrom, pathTo, filesList):
    # type: (Path, Path, list[Path]) -> None
    
    for fileFrom in filesList:
        fileRelative = Path(fileFrom.as_posix().replace(pathFrom.as_posix(), "")[1:])
        fileTo = (pathTo / fileRelative)
        shutil.copy2(fileFrom.as_posix(), ensurePath(fileTo).as_posix())


def removeEmptyDirs(path):
    # type: (Path) -> None
    
    for root, dirs, files in os.walk(path.as_posix(), topdown=False):
        root = Path(root).resolve()
        for _dir in dirs:
            _dir = root / _dir
            try:
                _dir.rmdir()
            except:
                pass


config = loadConfig(curPath)


if config is not None:
    dataFile = curPath.parent / config["DataFile"]
    
    if dataFile.exists():
        dataFile = dataFile.resolve()
        gameDir = getGameDir(config)
        tempDir = getTempDir(config)
        
        debugMsg("> Extract game data into temp directory...")
        decompressDataFile(dataFile, tempDir)
        
        filesLists = getFilesLists(gameDir)
        persistentFiles = filesLists[0]
        
        debugMsg("> Copy persistent files from game to temp directory...")
        copyPersistentFiles(gameDir, tempDir, persistentFiles)
        
        enginePath = curPath.parent / config["EnginePath"]
        
        if platform.system() != "Windows":
            os.system("chmod +x " + PLAT_QUOTE + enginePath.as_posix() + PLAT_QUOTE)
            
        extraArgs = " " + " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
        command = PLAT_QUOTE + enginePath.as_posix() + PLAT_QUOTE + extraArgs + " " + PLAT_QUOTE + config["MainFile"] + PLAT_QUOTE
        os.chdir(tempDir.as_posix())
        debugMsg("> Launch game in blenderplayer")
        subprocess.call(command, shell=True)
        sleep(0.2)
        
        filesLists = getFilesLists(tempDir)
        persistentFiles = filesLists[0]
        
        debugMsg("> Copy persistent files from temp to game directory...")
        copyPersistentFiles(tempDir, gameDir, persistentFiles)
        
        debugMsg("> Remove all files before finish...")
        for _file in filesLists[0] + filesLists[1]:
            _file.unlink()
            
        removeEmptyDirs(tempDir)
        os.chdir(tempDir.parent.as_posix())
        shutil.rmtree(tempDir.as_posix())
        
    else:
        print("X Could not find game data at", dataFile.as_posix())

