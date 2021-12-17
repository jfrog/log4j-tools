import os
import sys
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import IO
from zipfile import BadZipFile, ZipFile

JNDIMANAGER_CLASS_NAME = "log4j/core/net/JndiManager.class"
JNDILOOKUP_CLASS_NAME = "log4j/core/lookup/JndiLookup.class"
PATCH_STRING = b"allowedJndiProtocols"
PATCH_STRING_216 = b"log4j2.enableJndi"
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


@dataclass
class Diag:
    status: Status
    note: str


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
    (JndiLookupVer.v212_PATCH, JndiMgrVer.v212_PATCH): Diag(
        Status.FIX, "2.12.2 backport patch"
    ),
}


def confusion_message(filename: str, classname: str):
    print(
        f"Warning: {filename} contains multiple copies of {classname}; result may be invalid"
    )


def version_message(filename: str, diagnosis: Diag):
    messages = {
        Status.FIX: f"{GREEN}fixed{RESET_ALL}",
        Status.VULN: f"{RED}vulnerable{RESET_ALL}",
        Status.PARTIAL: f"{YELLOW}mitigated{RESET_ALL}",
        Status.INCONSISTENT: f"{RED}inconsistent{RESET_ALL}",
    }
    print(f"{filename}: {messages[diagnosis.status]}  {diagnosis.note}")


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
        return JndiMgrVer.v212_PATCH
    return JndiMgrVer.v20_v214


def test_file(file: IO[bytes], rel_path: str):
    try:
        with ZipFile(file) as jarfile:
            jndi_manager_status = JndiMgrVer.NOT_FOUND
            jndi_lookup_status = JndiLookupVer.NOT_FOUND

            for file_name in jarfile.namelist():
                if file_name.endswith(".jar"):
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
                        f"JndiLookup: {jndi_lookup_status.name}, JndiManager: {jndi_manager_status.name}",
                    ),
                )
                version_message(rel_path, diagnosis)

    except (IOError, BadZipFile):
        return


def acceptable_filename(filename: str):
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
            with open(root_dir, "rb") as file:
                test_file(file, "")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <root_folder>")
        exit()
    run_scanner(sys.argv[1])
