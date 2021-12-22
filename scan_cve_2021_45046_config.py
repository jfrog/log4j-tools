"""
Scans Log4j2 configuration files for lines that may enable exploitation of CVE-2021-45046
Requires Python 3.7
"""

from os import path
from pathlib import Path
from typing import Any, TextIO, BinaryIO
from zipfile import BadZipFile, ZipFile

import colorama
import easyargs

g_found_config_files = False

RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW

LOG4J_CONFIG_FILENAMES = ["log4j2", "log4j2-test"]
LOG4J_CONFIG_EXTENSIONS = [".properties", ".yaml", ".yml", ".json", ".jsn", ".xml"]
JAR_EXT_LIST = [".jar", ".war" , ".ear", ".sar"]

# Dangeorus patterns in config files that may indicate CVE-2021-45046 applicability
DANGEROUS_CONFIG_PATTERNS = ["${ctx:", "${sd:", "${map:"]

# Mapping between extension and comment character
EXT_TO_COMMENT_MAP = {
    ".xml": "<--",
    ".yaml": "#",
    ".yml": "#",
    ".properties": "#"
}


def is_log4j_configfile(file_path: str) -> bool:
    name, ext = path.splitext(path.basename(file_path))
    return name in LOG4J_CONFIG_FILENAMES and ext in LOG4J_CONFIG_EXTENSIONS


def test_jar_file(file: BinaryIO, jarfile_path: str) -> None:
    """ Scan JAR files for log4j configurations and recurse into child JAR files """
    try:
        with ZipFile(file) as jarfile:
            for file_path in jarfile.namelist():
                if any(file_path.endswith(jar_ext) for jar_ext in JAR_EXT_LIST):
                    # Recurse into a child JAR
                    next_file = jarfile.open(file_path, "r")
                    next_file_path = path.join(jarfile_path, file_path)
                    test_jar_file(next_file, next_file_path)
                elif is_log4j_configfile(file_path):
                    # Test the config file
                    next_file = jarfile.open(file_path, "r")
                    next_file_path = path.join(jarfile_path, file_path)
                    test_vulnerable_configfile(next_file, next_file_path)
    except (IOError, BadZipFile) as e:
        print(f"Caught exception: {str(e)}")


def normalize_config_line(line: Any, extension: str) -> str:
    normline = line

    # Convert bytes to str (will happen with config files opened within JARs)
    if isinstance(normline, bytes):
        normline = normline.decode("UTF-8")

    # Remove comment
    comment_char = EXT_TO_COMMENT_MAP.get(extension, "")
    if comment_char:
        normline = normline.partition(comment_char)[0]

    return normline


def test_vulnerable_configfile(file: TextIO, file_path: str) -> None:
    global g_found_config_files
    g_found_config_files = True

    extension = path.splitext(file_path)[1]
    conclusion = f"\n{file_path}: This configuration renders CVE-2021-45046"

    for i, line in enumerate(file):
        normline = normalize_config_line(line, extension)
        if any(dangerous_pattern in normline for dangerous_pattern in DANGEROUS_CONFIG_PATTERNS):
            print(f"{RED} {conclusion} potentially applicable")
            print(f"{RED} Found dangerous config line:\n#{i + 1} {normline}")
            return

    print(f"{GREEN}{conclusion} not applicable")


def scan_config_files(root_dir: str) -> None:
    for file_name in LOG4J_CONFIG_FILENAMES:
        for ext in LOG4J_CONFIG_EXTENSIONS:
            for file_path in Path(root_dir).rglob(file_name + ext):
                with open(file_path, "r") as f:
                    test_vulnerable_configfile(f, file_path)


def scan_jar_files(root_dir: str) -> None:
    for jar_ext in JAR_EXT_LIST:
        for file_path in Path(root_dir).rglob(f"*{jar_ext}"):
            with open(file_path, "rb") as f:
                test_jar_file(f, file_path)


@easyargs
def main(root_dir):
    colorama.init(autoreset=True)

    scan_config_files(root_dir)
    scan_jar_files(root_dir)

    if not g_found_config_files:
        print(f"{YELLOW} Did not find any log4j configuration files")


if __name__ == "__main__":
    main()
