import os
import sys
from collections import namedtuple
from enum import Enum, IntEnum, auto
from typing import IO, Set
from zipfile import BadZipFile, ZipFile

JNDIMANAGER_CLASS_NAME = "core/net/JndiManager.class"
JNDILOOKUP_CLASS_NAME = "core/lookup/JndiLookup.class"
PATCH_STRING = b"allowedJndiProtocols"
PATCH_STRING_216 = b"log4j2.enableJndi"
PATCH_STRING_217 = b"isJndiLookupEnabled"
PATCH_STRING_21 = b"LOOKUP"
PATCH_STRING_BACKPORT = b"JNDI is not supported"

RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RESET_ALL = "\x1b[0m"


class JndiMgrVer(IntEnum):
    NOT_FOUND = 0
    v20_v214 = auto()
    v215 = auto()
    v216 = auto()
    v217 = auto()
    v212_PATCH = auto()


class JndiLookupVer(IntEnum):
    NOT_FOUND = 0
    v20 = auto()
    v21_PLUS = auto()
    v212_PATCH = auto()


class Status(Enum):
    INCONSISTENT = auto()
    VULN = auto()
    PARTIAL = auto()
    FIX = auto()


Diag = namedtuple("Diag", ["status", "note"])


DIAGNOSIS_TABLE = {
    (JndiLookupVer.NOT_FOUND, JndiMgrVer.v212_PATCH): Diag(
        Status.FIX, "JndiLookup removed"
    ),
    (JndiLookupVer.NOT_FOUND, JndiMgrVer.v216): Diag(Status.FIX, "JndiLookup removed"),
    (JndiLookupVer.NOT_FOUND, JndiMgrVer.v215): Diag(Status.FIX, "JndiLookup removed"),
    (JndiLookupVer.NOT_FOUND, JndiMgrVer.v20_v214): Diag(
        Status.FIX, "JndiLookup removed"
    ),
    (JndiLookupVer.v20, JndiMgrVer.NOT_FOUND): Diag(
        Status.VULN, "Estimated version: 2.0"
    ),
    (JndiLookupVer.v21_PLUS, JndiMgrVer.v20_v214): Diag(
        Status.VULN, "Estimated version: 2.1 .. 2.14"
    ),
    (JndiLookupVer.v21_PLUS, JndiMgrVer.v215): Diag(
        Status.PARTIAL, "Estimated version: 2.15"
    ),
    (JndiLookupVer.v21_PLUS, JndiMgrVer.v216): Diag(
        Status.FIX, "Estimated version: 2.16"
    ),
    (JndiLookupVer.v21_PLUS, JndiMgrVer.v217): Diag(
        Status.FIX, "Estimated version: 2.17"
    ),
    (JndiLookupVer.v212_PATCH, JndiMgrVer.v212_PATCH): Diag(
        Status.FIX, "2.12.2 backport patch"
    ),
}


def confusion_message(filename: str, classname: str):
    print(
        "Warning: "
        + filename
        + " contains multiple copies of "
        + classname
        + "; result may be invalid"
    )


def version_message(filename: str, diagnosis: Diag):
    messages = {
        Status.FIX: GREEN + "fixed" + RESET_ALL,
        Status.VULN: RED + "vulnerable" + RESET_ALL,
        Status.PARTIAL: YELLOW + "mitigated" + RESET_ALL,
        Status.INCONSISTENT: RED + "inconsistent" + RESET_ALL,
    }
    print(filename + ": " + messages[diagnosis.status] + " " + diagnosis.note)


def class_version_jndi_lookup(classfile_content: bytes) -> JndiLookupVer:
    if PATCH_STRING_21 in classfile_content:
        return JndiLookupVer.v21_PLUS
    if PATCH_STRING_BACKPORT in classfile_content:
        return JndiLookupVer.v212_PATCH
    return JndiLookupVer.v20


def class_version_jndi_manager(classfile_content: bytes) -> JndiMgrVer:
    if PATCH_STRING in classfile_content:
        if PATCH_STRING_216 in classfile_content:
            return JndiMgrVer.v216
        return JndiMgrVer.v215
    elif PATCH_STRING_216 in classfile_content:
        if PATCH_STRING_217 in classfile_content:
            return JndiMgrVer.v217
        else:
            return JndiMgrVer.v212_PATCH
    return JndiMgrVer.v20_v214


def test_file(file: IO[bytes], rel_path: str):
    try:
        with ZipFile(file) as jarfile:
            jndi_manager_status = JndiMgrVer.NOT_FOUND
            jndi_lookup_status = JndiLookupVer.NOT_FOUND

            for file_name in jarfile.namelist():
                if acceptable_filename(file_name):
                    next_file = jarfile.open(file_name, "r")
                    test_file(next_file, os.path.join(rel_path, file_name))
                    continue

                if file_name.endswith(JNDIMANAGER_CLASS_NAME):
                    if jndi_manager_status != JndiMgrVer.NOT_FOUND:
                        confusion_message(file_name, JNDIMANAGER_CLASS_NAME)
                    classfile_content = jarfile.read(file_name)
                    jndi_manager_status = class_version_jndi_manager(classfile_content)
                    continue

                if file_name.endswith(JNDILOOKUP_CLASS_NAME):
                    if jndi_lookup_status != JndiLookupVer.NOT_FOUND:
                        confusion_message(file_name, JNDILOOKUP_CLASS_NAME)
                    classfile_content = jarfile.read(file_name)
                    jndi_lookup_status = class_version_jndi_lookup(classfile_content)

            # went over all the files in the current layer; draw conclusions
            if jndi_lookup_status or jndi_manager_status:
                diagnosis = DIAGNOSIS_TABLE.get(
                    (jndi_lookup_status, jndi_manager_status),
                    Diag(
                        Status.INCONSISTENT,
                        "JndiLookup: "
                        + jndi_lookup_status.name
                        + ", JndiManager: "
                        + jndi_manager_status.name,
                    ),
                )
                version_message(rel_path, diagnosis)

    except (IOError, BadZipFile):
        return
    except RuntimeError as e:
        print(rel_path + ": " + str(e))
        return


def acceptable_filename(filename: str):
    return any(filename.endswith(ext) for ext in [".jar", ".war", ".sar", ".ear", ".par", ".zip"])


def run_scanner(root_dir: str, exclude_dirs: Set[str]):
    if os.path.isdir(root_dir):
        for directory, dirs, files in os.walk(root_dir, topdown=True):
            [
                dirs.remove(excluded_dir)
                for excluded_dir in list(dirs)
                if os.path.join(directory, excluded_dir) in exclude_dirs
            ]

            for filename in files:
                if acceptable_filename(filename):
                    full_path = os.path.join(directory, filename)
                    rel_path = os.path.relpath(full_path, root_dir)
                    try:
                        with open(full_path, "rb") as file:
                            test_file(file, rel_path)
                    except FileNotFoundError as fnf_error:
                        print(fnf_error)
    elif os.path.isfile(root_dir):
        if acceptable_filename(root_dir):
            with open(root_dir, "rb") as file:
                test_file(file, "")


def print_usage():
    print("Usage: " + sys.argv[0] + " <root_folder> [-exclude <folder1> <folder2> ...]")
    print("or: " + sys.argv[0] + " <archive_file>")
    exit()


def parse_command_line():
    if len(sys.argv) < 2 or len(sys.argv) == 3:
        print_usage()

    root_dir = sys.argv[1]
    exclude_folders = []
    if len(sys.argv) > 3:
        if sys.argv[2] != "-exclude":
            print_usage()
        exclude_folders = sys.argv[3:]
    return root_dir, exclude_folders


if __name__ == "__main__":

    root_dir, exclude_dirs = parse_command_line()

    for dir_to_check in exclude_dirs:
        if not os.path.isdir(dir_to_check):
            print(dir_to_check + " is not a directory")
            print_usage()
    if not os.path.isdir(root_dir) and not (
        os.path.isfile(root_dir) and acceptable_filename(root_dir)
    ):
        print(root_dir + " is not a directory or an archive")
        print_usage()

    print("Scanning " + root_dir)
    if exclude_dirs:
        print("Excluded: " + ", ".join(exclude_dirs))

    run_scanner(root_dir, set(exclude_dirs))
