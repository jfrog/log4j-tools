import os
import sys
from collections import namedtuple
from enum import Enum, IntEnum
from typing import IO, Set
from zipfile import ZipFile, BadZipfile
from tarfile import open as tar_open
from tarfile import CompressionError, ReadError
from io import BytesIO

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

ZIP_EXTENSIONS = {".jar", ".war", ".sar", ".ear", ".par", ".zip"}
TAR_EXTENSIONS = {".gz", ".tar"}


class JndiMgrVer(IntEnum):
    NOT_FOUND = 0
    v20_v214 = 1
    v215 = 2
    v216 = 3
    v217 = 4
    v212_PATCH = 5


class JndiLookupVer(IntEnum):
    NOT_FOUND = 0
    v20 = 1
    v21_PLUS = 2
    v212_PATCH = 3


class Status(Enum):
    INCONSISTENT = 0
    VULN = 1
    PARTIAL = 2
    FIX = 3


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


def confusion_message(filename, classname):
    print(
        "Warning: "
        + filename
        + " contains multiple copies of "
        + classname
        + "; result may be invalid"
    )


def version_message(filename, diagnosis):
    messages = {
        Status.FIX: GREEN + "fixed" + RESET_ALL,
        Status.VULN: RED + "vulnerable" + RESET_ALL,
        Status.PARTIAL: YELLOW + "mitigated" + RESET_ALL,
        Status.INCONSISTENT: RED + "inconsistent" + RESET_ALL,
    }
    print(filename + " >> " + messages[diagnosis.status] + " " + diagnosis.note)


def class_version_jndi_lookup(classfile_content):
    if PATCH_STRING_21 in classfile_content:
        return JndiLookupVer.v21_PLUS
    if PATCH_STRING_BACKPORT in classfile_content:
        return JndiLookupVer.v212_PATCH
    return JndiLookupVer.v20


def class_version_jndi_manager(classfile_content):
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


def zip_file(file, rel_path, silent_mode):
    try:
        jarfile = ZipFile(file)
        jndi_manager_status = JndiMgrVer.NOT_FOUND
        jndi_lookup_status = JndiLookupVer.NOT_FOUND

        for file_name in jarfile.namelist():
            if acceptable_filename(file_name):
                next_file = jarfile.open(file_name, "r")
                test_file(
                    BytesIO(next_file.read()),
                    os.path.join(rel_path, file_name),
                    silent_mode,
                )
                continue

            if file_name.endswith(JNDIMANAGER_CLASS_NAME):
                if jndi_manager_status != JndiMgrVer.NOT_FOUND:
                    if not silent_mode:
                        confusion_message(file_name, JNDIMANAGER_CLASS_NAME)
                classfile_content = jarfile.read(file_name)
                jndi_manager_status = class_version_jndi_manager(classfile_content)
                continue

            if file_name.endswith(JNDILOOKUP_CLASS_NAME):
                if jndi_lookup_status != JndiLookupVer.NOT_FOUND:
                    if not silent_mode:
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
    except IOError:
        return
    except BadZipfile as e:
        if not silent_mode:
            print(rel_path + ": " + str(e))
        return
    except RuntimeError as e:
        if not silent_mode:
            print(rel_path + ": " + str(e))
        return


def tar_file(file, rel_path, silent_mode):
    try:
        with tar_open(fileobj=file) as tarfile:
            for item in tarfile.getmembers():
                if "../" in item.name:
                    continue
                if item.isfile() and acceptable_filename(item.name):
                    fileobj = tarfile.extractfile(item)
                    new_path = rel_path + "/" + item.name
                    test_file(fileobj, new_path)
                item = tarfile.next()
    except (EnvironmentError, RuntimeError, CompressionError, ReadError) as e:
        if not silent_mode:
            print(rel_path + ": " + str(e))
        return


def test_file(file, rel_path, silent_mode):
    if any(rel_path.endswith(ext) for ext in ZIP_EXTENSIONS):
        zip_file(file, rel_path, silent_mode)

    elif any(rel_path.endswith(ext) for ext in TAR_EXTENSIONS):
        tar_file(file, rel_path, silent_mode)


def acceptable_filename(filename):
    return any(filename.endswith(ext) for ext in ZIP_EXTENSIONS | TAR_EXTENSIONS)


def run_scanner(root_dir, exclude_dirs, silent_mode):
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
                            test_file(file, rel_path, silent_mode)
                    except EnvironmentError as fnf_error:
                        if not silent_mode:
                            print(filename + ": " + str(fnf_error))

    elif os.path.isfile(root_dir):
        if acceptable_filename(root_dir):
            with open(root_dir, "rb") as file:
                test_file(file, "", silent_mode)


def print_usage():
    print("Usage: " + sys.argv[0] + " <root_folder> [-exclude <folder1> <folder2> ...]")
    print("or: " + sys.argv[0] + " <archive_file>")
    exit()


def parse_command_line():
    if len(sys.argv) < 2:
        print_usage()

    root_dir = sys.argv[1]
    exclude_folders = []

    silent = len(sys.argv) > 2 and sys.argv[2] == "-quiet"
    exclude_start = 3 if silent else 2
    if len(sys.argv) > exclude_start:
        if not sys.argv[exclude_start] == "-exclude":
            print_usage()
        exclude_folders = sys.argv[exclude_start + 1 :]

    return root_dir, exclude_folders, silent


if __name__ == "__main__":

    root_dir, exclude_dirs, silent_mode = parse_command_line()

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

    run_scanner(root_dir, set(exclude_dirs), silent_mode)
