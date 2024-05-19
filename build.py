import sys
import os
import subprocess
import shutil
import fnmatch
from pathlib import Path


curDir = Path(__file__).parent.absolute()
pythonExecutable = Path(sys.executable).absolute()


def main():
    # type: () -> None
    
    os.chdir(curDir.as_posix())
    
    if sys.argv[-1] in operators.keys():
        operators[sys.argv[-1]]()
    
    else:
        print("X Invalid command:", sys.argv[-1])
        print("Available commands:", ", ".join([i for i in operators.keys()]))


def build(target):
    # type: (str) -> None
    
    toolchain = "i686-pc-windows-gnu" if target == "windows" else "i686-unknown-linux-gnu"
    ext = ".exe" if target == "windows" else ""
    launcherSourcePath = (curDir / "launcher/rust").absolute()
    sourceExe = (curDir / "launcher/rust/target/{toolchain}/release/rangearmor{ext}".format(toolchain=toolchain, ext=ext)).absolute()
    targetExe = (curDir / ("build_files/release/launcher/Launcher" + ext)).absolute()
    
    print("> Started build for target:", toolchain)
    
    if targetExe.exists():
        print("> Deleted existing executable:", targetExe.as_posix())
        targetExe.unlink()
        
    os.chdir(launcherSourcePath.as_posix())
    args = ["cargo", "build", "--target=" + toolchain, "--release"]
    print("> Running cargo build:", " ".join(args))
    subprocess.call(args)
    os.chdir(curDir.as_posix())
    
    print("> Copying executable to:", targetExe.as_posix())
    shutil.copy2(sourceExe.as_posix(), targetExe.as_posix())

    args = ["upx", "-9", targetExe.as_posix()]
    print("> Running UPX on executable:", " ".join(args))
    subprocess.call(args)
    
    print("> Done!")


def minify():
    # type: () -> None
    
    script = curDir / "launcher/python/scripts/minify_launcher.py"
    subprocess.call([pythonExecutable.as_posix(), script.as_posix()])


def clean():
    # type: () -> None
    
    directory = curDir / "launcher/rust/target"
    
    if directory.exists():
        print("> Deleting directory:", directory.as_posix())
        shutil.rmtree(directory.as_posix())


def export(_target):
    # type: (str) -> None
    
    minify()
    
    projectFile = (curDir / "godot/project.godot").absolute()
    exportPath = (curDir / "godot/bin").absolute()
    
    if not exportPath.exists():
        exportPath.mkdir()
        (exportPath / ".gdignore").touch()
        
    targets = {
        "Windows64": "Windows Desktop 64",
        "Linux64": "Linux 64",
    }
    
    for target in targets.keys():
        
        if _target == "All" or target.startswith(_target):
            name = targets[target]
            targetPath = (exportPath / target).absolute()
            
            if targetPath.exists():
                shutil.rmtree(targetPath.as_posix())
            
            targetPath.mkdir()
            
            print("> Exporting for target:", name)
            args = ["godot", "--export-debug", name, "--no-window", projectFile.as_posix()]
            print("  > Running Godot export:", " ".join(args))
            subprocess.call(args)
            
            print("  > Copying release files to:", targetPath.as_posix())
            shutil.copytree((curDir / "build_files/release").as_posix(), (targetPath / "release").as_posix())
            
            print("  > Deleting ignored files from:", targetPath.as_posix())
            ignoredPatterns = [".gitignore", ".gitkeep", "__pycache__"]
            
            for pattern in ignoredPatterns:
                for folder, subfolders, files in os.walk(targetPath.as_posix()):
                    items = subfolders + files
                    
                    for item in items:
                        curItem = (Path(folder) / item).absolute()
                        
                        if fnmatch.fnmatch(curItem.name, pattern):
                            
                            if curItem.is_file():
                                print("    > Deleted file:", curItem.as_posix())
                                curItem.unlink()
                            
                            elif curItem.is_dir():
                                print("    > Deleted directory:", curItem.as_posix())
                                shutil.rmtree(curItem.as_posix())
    
    print("> Done!")


operators = {
    "clean": lambda: clean(),
    "export": lambda: export("All"),
    "export_windows": lambda: export("Windows"),
    "export_linux": lambda: export("Linux"),
    "launcher_windows": lambda: build("windows"),
    "launcher_linux": lambda: build("linux"),
    "minify": lambda: minify(),
}  # type: dict[str, object]


main()
