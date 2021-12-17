import os
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Set, Tuple
from zipfile import BadZipFile, ZipFile

import easyargs
from colorama import Fore, Style
from jawa.classloader import ClassLoader
from jawa.constants import InterfaceMethodRef, MethodReference
from jawa.methods import Method
from tqdm import tqdm


class JVMOpcodes(IntEnum):
    INVOKEVIRTUAL = 182
    INVOKESPECIAL = 183
    INVOKESTATIC = 184
    INVOKEINTERFACE = 185
    INVOKEDYNAMIC = 186


INVOKE_OPCODES = {
    JVMOpcodes.INVOKEVIRTUAL,
    JVMOpcodes.INVOKESPECIAL,
    JVMOpcodes.INVOKESTATIC,
    JVMOpcodes.INVOKEINTERFACE,
    JVMOpcodes.INVOKEDYNAMIC,
}


@dataclass(frozen=True)
class CallTarget:
    class_name: str
    method_name: str
    method_type: str


def print_file_name(filename):
    tqdm.write(f"\n\n\nProcessing .jar file:\n{filename}")


def print_caller_results(class_name, calling_methods_by_target):
    if calling_methods_by_target:
        # collapse method types:
        calling_methods_collapsed = {
            CallTarget(ct.class_name, ct.method_name, ""): calling_methods_by_target[ct]
            for ct in calling_methods_by_target
        }

        tqdm.write(f"\nClass: {Fore.GREEN}{class_name}{Style.RESET_ALL}")
        tqdm.write("Vulnerable call | Methods")
        tqdm.write("----------------+---------")
        for callee, callers in calling_methods_collapsed.items():
            tqdm.write(
                Fore.RED
                + f"{callee.method_name:15}"
                + Style.RESET_ALL
                + " | "
                + ", ".join(callers)
            )


def print_matching_classes(classes):
    tqdm.write(f"\nClasses found:")
    tqdm.write(", ".join([Fore.GREEN + c + Style.RESET_ALL for c in classes]))


def jar_quickmatch(filename, match_string):
    try:
        with ZipFile(filename) as jarfile:
            classes = [name for name in jarfile.namelist() if name.endswith(".class")]
            for c in classes:
                classfile_content = jarfile.read(c)
                if match_string in classfile_content:
                    return True
            return False
    except (IOError, BadZipFile):
        tqdm.write(f"Could not open file: {filename}")


class XrefAnalysis:
    def __init__(self, filename, class_regex, method_regex):
        self.class_regex_compiled = re.compile(class_regex)
        self.method_regex_compiled = re.compile(method_regex)
        self.class_loader = ClassLoader(filename)
        self.methods, self.callers = self.traverse(self.class_loader)

    def get_matching_classes(self):
        classes = {
            class_name
            for class_name in self.class_loader.classes
            if self.class_regex_compiled.match(class_name)
        }
        return classes

    def get_calling_classes(self):
        calling_classes = set()
        for callee, caller_set in self.callers.items():
            if self.class_regex_compiled.match(
                callee.class_name
            ) and self.method_regex_compiled.match(callee.method_name):
                calling_classes |= caller_set
        return calling_classes

    @staticmethod
    def method_ref_to_call_target(method_ref):
        if method_ref and isinstance(method_ref, (MethodReference, InterfaceMethodRef)):
            return CallTarget(
                method_ref.class_.name.value,
                method_ref.name_and_type.name.value,
                method_ref.name_and_type.descriptor.value,
            )
        return None

    def traverse(self, classloader: ClassLoader):
        call_targets = {}
        methods = {}
        callers = defaultdict(set)
        for class_name in classloader.classes:
            try:
                classloader[class_name]
            except IndexError:
                continue
            (
                call_targets[class_name],
                methods[class_name],
            ) = self.summarize_class(classloader[class_name])

        for class_name, class_call_targets in call_targets.items():
            for call_target in class_call_targets:
                callers[call_target].add(class_name)

        return methods, callers

    def summarize_class(self, classfile) -> Tuple[Set[CallTarget], List[Method]]:
        class_callees: Set[CallTarget] = set()
        for const in classfile.constants:
            call_target = self.method_ref_to_call_target(const)
            if call_target:
                class_callees.add(call_target)
        methods = list(classfile.methods)
        return class_callees, methods

    def analyze_class(self, classname):
        all_xrefs = set()
        xref_constants = defaultdict(set)
        calling_methods_by_target = defaultdict(set)
        for method in self.methods[classname]:
            new_xrefs = callsites_in_method(method)
            if not new_xrefs:
                continue
            for xref in new_xrefs:
                xref_constants[xref].add(method.name.value)
            all_xrefs |= new_xrefs

        interesting_xrefs = {}
        for xref in all_xrefs:
            call_target = self.method_ref_to_call_target(
                self.class_loader[classname].constants.get(xref)
            )
            if call_target:
                if self.class_regex_compiled.match(
                    call_target.class_name
                ) and self.method_regex_compiled.match(call_target.method_name):
                    interesting_xrefs[xref] = call_target

        for xref in interesting_xrefs:
            calling_methods_by_target[interesting_xrefs[xref]] |= xref_constants[xref]
        return calling_methods_by_target


def callsites_in_method(method: Method):
    if not method.code:
        return
    method_code = method.code.disassemble()
    return {op.operands[0].value for op in method_code if op.opcode in INVOKE_OPCODES}


def traverse_folder(root_dir, quickmatch_string, do_quickmatch):
    print(f"Walking {root_dir}...")
    files_to_scan = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.endswith(".jar"):
                full_name = os.path.join(root, f)
                if not do_quickmatch or jar_quickmatch(full_name, quickmatch_string):
                    files_to_scan.append(full_name)
    return files_to_scan


def print_xrefs_analysis(xref_analysis, filename):
    first = True
    for classname in xref_analysis.get_calling_classes():
        calling_methods_by_target = xref_analysis.analyze_class(classname)

        if calling_methods_by_target:
            if first:
                first = False
                print_file_name(filename)
            print_caller_results(classname, calling_methods_by_target)


def print_class_existence(xref_analysis, filename):
    matching_classes = xref_analysis.get_matching_classes()
    if matching_classes:
        print_file_name(filename)
        print_matching_classes(matching_classes)


@easyargs
def run_scanner(
    root_dir,
    # regex for class name filtering
    class_regex="org/apache/logging/log4j/Logger",
    # regex for method name filtering (ignored when looking for existence of classes)
    method_regex="(info|warn|error|log|debug|trace|fatal|catching|throwing|traceEntry|printf|logMessage)",
    # checking for existence of this string in classes unless no_quickmatch
    quickmatch_string="log4j",
    # not set - looking for calls to specified methods, set - looking for existence of classes
    class_existence=False,
    # when set, do not do quick match
    no_quickmatch=False,
):
    if not no_quickmatch:
        tqdm.write(f"Precondition grep filter: {quickmatch_string}")
    if class_existence:
        tqdm.write(f"Looking for presence of classes: {class_regex}")
    else:
        tqdm.write(
            f"Looking for calls to: class pattern {class_regex}, method name pattern: {method_regex}"
        )
    tqdm.write("Scanning folder for .jar files")

    files_to_scan = traverse_folder(
        root_dir, quickmatch_string.encode("utf-8"), not no_quickmatch
    )

    for filename in tqdm(files_to_scan):
        try:
            xref_analysis = XrefAnalysis(filename, class_regex, method_regex)
            if class_existence:
                print_class_existence(xref_analysis, os.path.relpath(filename, root_dir))
            else:
                print_xrefs_analysis(xref_analysis, os.path.relpath(filename, root_dir))
        except ValueError as e:
            tqdm.write(f"Parsing error in {filename}")



if __name__ == "__main__":
    run_scanner()
