import os
import sys
import shutil
import platform

from pathlib import Path
from time import time, sleep


# Constants
_DEBUG = False
PLAT_QUOTE = '"' if platform.system() == "Windows" else "'"
ITEM_SEPARATOR = "\t"


# Globals
curPath = Path(__file__).resolve().parent
rootPath = curPath.parent
curPlatform = platform.system()


def main():
    import subprocess

    if config is not None:
        gameDataFile = curPath.parent / config["DataSource"]  # type: Path

        if gameDataFile.exists():
            enginePath = curPath.parent / config["EnginePath"]  # type: Path

            if platform.system() != "Windows":
                os.system("chmod +x " + PLAT_QUOTE + enginePath.as_posix() + PLAT_QUOTE)

            showConsoleWindow(False)
            
            extraArgs = " " + args.get("-a").strip('"\' ') if args.get("-a") else ""
            console = " -c" if args.get("-c") and not "-c" in extraArgs else ""
            command = PLAT_QUOTE + enginePath.as_posix() + PLAT_QUOTE + console + extraArgs + " " + PLAT_QUOTE + config["MainFile"] + PLAT_QUOTE
            os.chdir(gameDataFile.as_posix())
            debugMsg("> Launch game in RangePlayer")
            if platform.system() == "Windows": subprocess.call(command, shell=False)
            else: subprocess.call(command, shell=True)
            showConsoleWindow(False)
            sleep(0.2)

            showConsoleWindow(True)

        else:
            print("X Could not find game data at", gameDataFile.as_posix())


def debugMsg(*args, waitInput=False):
    # type: (object, bool) -> None

    if _DEBUG:
        finalMsg = ""
        for arg in args: finalMsg += str(arg)
        print(finalMsg)
        if waitInput: input("Press any key to continue...")


def parseArgs():
    # type: () -> dict[str, str]

    def getArgName(arg):
        # type: (str) -> str

        result = arg

        if arg.startswith("--"):
            result = "-"

            for c in arg:
                if c != "-":
                    result += c
                    break

        return result

    args = {}  # type: dict[str, str]

    if len(sys.argv) > 1:
        for i in range(len(sys.argv)):
            if i > 0:
                item = sys.argv[i]

                if item.startswith("-"):
                    args[getArgName(item)] = "True"

                    if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
                        args[getArgName(item)] = sys.argv[i + 1]

    return args


def loadConfig(args):
    # type: (dict[str, str]) -> None

    import json
    from ast import literal_eval

    config = {}  # type: dict[str, object]
    configPath = (curPath / "config.json") if not args.get("-f") else Path(args.get("-f").strip('"\' '))
    engineCandidates = [curPlatform + "32", curPlatform + "64"] if not args.get("-e") else [args.get("-e")]
    enginePath = None  # type: Path

    if configPath.exists():

        with open(configPath.as_posix(), "r") as sourceFile:
            fileParsed = False

            try:
                config = json.loads(sourceFile.read())
                fileParsed = True
            except:
                try:
                    config = literal_eval(sourceFile.read())
                    fileParsed = True
                except:
                    print("X Could not parse config file at", configPath.as_posix())
                    return config

            if fileParsed:
                print("> Read config from", configPath.as_posix())

        for candidate in engineCandidates:
            candidate = rootPath / (config.get("Engine" + candidate, ""))  # type: Path

            if candidate.exists() and candidate.is_file():
                enginePath = candidate.resolve()
                break

        if enginePath and enginePath.exists():
                config["EnginePath"] = enginePath.as_posix()
                print("> Read engine path from", enginePath.as_posix())

        else:
            print("X Could not find suitable engine executable")

    else:
        print("X Could not find config file at", configPath)

    return config


def getGameDir(config):
    # type: (dict[str, object]) -> Path

    import string

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

    from hashlib import md5

    tempDir = Path.home()
    tempDirName = md5(("RangeArmor" + str(time())).encode()).hexdigest().upper()

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

    import glob
    import os
    from fnmatch import fnmatchcase

    persistentFiles = [] # type: list[Path]
    generalFiles = [] # type: list[Path]

    # Populate persistent files list
    for _folder, _subfolders, _files in os.walk(path.as_posix()):
        for _file in _files:
            _file = Path(_folder) / _file
            pathToMatch = _file.as_posix().replace(path.as_posix(), "")

            for pattern in config["Persistent"]:
                if fnmatchcase(pathToMatch, pattern):
                    persistentFiles.append(_file.resolve())

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

    import zlib
    import base64
    from ast import literal_eval

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
        fileTo = (fileRelative / pathTo)
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


def showConsoleWindow(show):
    # type: (bool) -> None

    if platform.system() == "Windows" and not args.get("-c"):
        import ctypes

        SW_HIDE = 0
        SW_SHOW = 5
        show = SW_SHOW if show else SW_HIDE

        try:
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            window = kernel32.GetConsoleWindow()

            if window:
                user32.ShowWindow(window, show)

        except Exception as e:
            print("X Could not hide console window:", e)


args = parseArgs()
config = loadConfig(args)

if config:
    try:
        main()
    except Exception as e:
        showConsoleWindow(True)
        print("X Error while executing game:", e)
