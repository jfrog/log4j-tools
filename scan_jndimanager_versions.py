import os
import sys
from typing import IO
from zipfile import BadZipFile, ZipFile

CLASS_NAME = "log4j/core/net/JndiManager.class"
PATCH_STRING = b"allowedJndiProtocols"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
RESET_ALL = "\x1b[0m"


def bad_message(filename: str):
    print(f"{filename}: {RED}vulnerable JndiManager found{RESET_ALL}")


def good_message(filename: str):
    print(f"{filename}: {GREEN}fixed JndiManager found{RESET_ALL}")


def test_file(file: IO[bytes], rel_path: str):
    found_vulnerable_class = False
    try:
        with ZipFile(file) as jarfile:
            for file_name in jarfile.namelist():
                if file_name.endswith(".jar"):
                    next_file = jarfile.open(file_name, "r")
                    test_file(next_file, os.path.join(rel_path, file_name))
                    continue
                if not file_name.endswith(CLASS_NAME):
                    continue

                found_vulnerable_class = True
                classfile_content = jarfile.read(file_name)
                if PATCH_STRING in classfile_content:
                    good_message(rel_path)
                    return
        if found_vulnerable_class:
            bad_message(rel_path)
    except (IOError, BadZipFile):
        return


def acceptable_filename(filename):
    return filename.endswith(".jar") or filename.endswith(".war")


def run_scanner(root_dir: str):
    if os.path.isdir(root_dir):
        print("Scanning...")
        for directory, dirs, files in os.walk(root_dir):
            for filename in files:
                if acceptable_filename(filename):
                    full_path = os.path.join(directory, filename)
                    rel_path = os.path.relpath(full_path, root_dir)
                    with open(full_path, "rb") as file:
                        test_file(file, rel_path)
    elif os.path.isfile(root_dir):
        if acceptable_filename(root_dir):
            with open(root_dir, 'rb') as file:
                test_file(file, "")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <root_folder>")
        exit()
    run_scanner(sys.argv[1])
